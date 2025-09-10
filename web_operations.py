from dotenv import load_dotenv
import requests
import os
from urllib.parse import quote_plus

from snapshot_operations import poll_snapshot_status, download_snapshot

load_dotenv()

dataset_id = "gd_lvz8ah06191smkebj4"

def _make_api_request(url, **kwargs):
    api_key = os.getenv("BRIGHTDATA_API_KEY")

    headers = {
        "Authorization" : f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers = headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def serp_search(query, engine = "google"):
    if engine == "google":
        base_url = "https://www.google.com/search"
    
    elif engine == "bing":
        base_url = "https://www.bing.com/search"    
    
    else:
        raise ValueError(f"Unsupported search engine: {engine}")
    
    url = "https://api.brightdata.com/request"

    payload = {
        "zone": "langflow_ai_agent",
        "url": f"{base_url}?q={quote_plus(query)}&brd_json=1",
        "format": "raw"
    }

    full_response = _make_api_request(url, json=payload)

    if not full_response:
        return None
    
    extracted_data = {
        "knowledge": full_response.get("knowledge", {}),
        "organic": full_response.get("organic", []),
    }

    return extracted_data


def _trigger_and_download_snapshot(trigger_url, params, data, operation_name="operation"):
    trigger_result = _make_api_request(trigger_url, params=params, json=data)
    if not trigger_result:
        print(f"{operation_name} trigger failed.")
        return None
    
    snapshot_id = trigger_result.get("snapshot_id")
    if not snapshot_id:
        print(f"{operation_name} trigger did not return a snapshot_id.")
        return None
    

    if not poll_snapshot_status(snapshot_id):
        print(f"{operation_name} snapshot processing failed or timed out.")
        return None
    
    raw_data = download_snapshot(snapshot_id)
    if not raw_data:
        print(f"{operation_name} data download failed.")
        return None
    return raw_data



def reddit_search_api(keyword, date = "All time", sort_by = "Hot", num_of_posts = 75):
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"

    params = {
        "dataset_id": dataset_id,
        "include_errors": "true",
        "type": "discover_new",
        "discover_by": "keyword"
    }

    data =[
        {
            "keyword": keyword,
            "date": date,
            "sort_by": sort_by,
            "num_of_posts": num_of_posts
        }
    ]

    raw_data = _trigger_and_download_snapshot(trigger_url, params, data, operation_name="Reddit search")

    if not raw_data:
        return None
    
    parsed_data = []
    for post in raw_data:
        parsed_post = {
            "title": post.get("title"),
            "url": post.get("url"),
            
        }
        parsed_data.append(parsed_post)

    return {"parsed_posts": parsed_data, "total_found": len(parsed_data)}
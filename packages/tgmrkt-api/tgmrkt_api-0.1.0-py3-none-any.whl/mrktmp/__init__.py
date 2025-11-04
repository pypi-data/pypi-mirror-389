from .client import MrktClient
import requests
import csv
import json
from datetime import datetime
import time

__version__ = "0.3.0"
__all__ = [
    'get_token', 'search_gifts', 'my_gifts', 'list_for_sale', 'buy_gift',
    'get_sticker_collections', 'get_user_info', 'get_competitions', 'get_stars_gifts',
    'get_all_gift_names', 'nano_to_ton', 'get_collection_floors_from_saling',
    'get_top_floors', 'get_collection_floor', 'get_collection_stats',
    'monitor_floors', 'export_to_csv', 'export_collection_floors',
    'parse_collection_full'
]


def get_token(init_data: str) -> str:
    """Get auth token from Telegram init_data (POST /auth)."""
    url = "https://api.tgmrkt.io/api/v1/auth"
    data = {"data": init_data}
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        return resp.json().get("token", "")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to get token: {e}")


def search_gifts(auth_data: str, collection_names: list = None, model_names: list = None,
                 backdrop_names: list = None, symbol_names: list = None, count: int = 20, cursor: str = ""):
    """Search gifts with filters (POST /gifts/saling)."""
    client = MrktClient(auth_data)
    data = {
        "collectionNames": collection_names or [],
        "modelNames": model_names or [],
        "backdropNames": backdrop_names or [],
        "symbolNames": symbol_names or [],
        "ordering": "Price",
        "lowToHigh": True,
        "maxPrice": None,
        "minPrice": None,
        "mintable": None,
        "number": None,
        "count": min(count, 20),
        "cursor": cursor,
        "query": None,
        "promotedFirst": False
    }
    return client._request("POST", "/gifts/saling", json=data)


def my_gifts(auth_data: str, count: int = 20, cursor: str = ""):
    """Get my/visible gifts (POST /gifts/saling with empty filters)."""
    return search_gifts(auth_data, count=count, cursor=cursor)


def list_for_sale(auth_data: str, gift_id: str, price_ton: float):
    """List gift for sale (placeholder - capture POST body from Network tab)."""
    client = MrktClient(auth_data)
    data = {"giftId": gift_id, "price": int(price_ton * 1_000_000_000)}
    return client._request("POST", "/listings/create", json=data)


def buy_gift(auth_data: str, gift_id: str):
    """Buy gift (placeholder - capture POST body from Network tab)."""
    client = MrktClient(auth_data)
    data = {"giftId": gift_id}
    return client._request("POST", "/gifts/buy", json=data)


def get_sticker_collections(auth_data: str):
    """Get sticker collections (GET /sticker-sets/collections)."""
    client = MrktClient(auth_data)
    return client._request("GET", "/sticker-sets/collections")


def get_user_info(auth_data: str):
    """Get user profile info (GET /user/me - may return 404)."""
    client = MrktClient(auth_data)
    try:
        return client._request("GET", "/user/me")
    except ValueError:
        return {"error": "Endpoint not available"}


def get_competitions(auth_data: str):
    """Get active competitions/events (GET /competitions)."""
    client = MrktClient(auth_data)
    return client._request("GET", "/competitions")


def get_stars_gifts(auth_data: str, cursor: str = ""):
    """Get Telegram Stars gifts (POST /stars-gifts)."""
    client = MrktClient(auth_data)
    data = {"cursor": cursor}
    return client._request("POST", "/stars-gifts", json=data)


def get_all_gift_names(auth_data: str, max_count: int = 1000):
    """Get all unique gift names with pagination."""
    all_names = set()
    cursor = ""
    count = 0

    while count < max_count:
        try:
            resp = search_gifts(auth_data, count=20, cursor=cursor)
            gifts_list = resp.get('gifts', [])

            if not gifts_list:
                break

            for gift in gifts_list:
                all_names.add(gift.get('name', ''))
                count += 1
                if count >= max_count:
                    break

            cursor = resp.get('cursor', '')
            if not cursor:
                break

            print(f"Loaded {len(all_names)} unique names...")
        except Exception as e:
            print(f"Error loading names: {e}")
            break

    return sorted(list(all_names))


def nano_to_ton(nano: int) -> float:
    """Convert nanoTON to TON."""
    return nano / 1_000_000_000 if nano else 0.0


def get_collection_floors_from_saling(auth_data: str, max_pages: int = 10):
    """Get floor price for each collection from /gifts/saling (groups by collection, takes MIN price)."""
    floors = {}
    cursor = ""
    page = 0

    try:
        while page < max_pages:
            resp = search_gifts(auth_data, count=20, cursor=cursor)
            gifts_list = resp.get('gifts', [])

            if not gifts_list:
                break

            for gift in gifts_list:
                if gift.get('isOnSale'):
                    coll = gift.get('collectionName', 'Unknown')
                    price = gift.get('salePrice', float('inf'))

                    if coll not in floors:
                        floors[coll] = price
                    else:
                        floors[coll] = min(floors[coll], price)

            cursor = resp.get('cursor', '')
            if not cursor:
                break

            page += 1
            print(f"Page {page}: found {len(floors)} collections...")
    except Exception as e:
        print(f"Error getting floors: {e}")

    return {coll: nano_to_ton(price) for coll, price in floors.items()}


def get_top_floors(auth_data: str, n: int = 5):
    """Get top N collections by floor price (ascending, in TON)."""
    try:
        collections = get_sticker_collections(auth_data)
        top = sorted(collections, key=lambda c: c.get('floorPriceNanoTons', 0))[:n]
        return {c['title']: nano_to_ton(c['floorPriceNanoTons']) for c in top}
    except Exception as e:
        print(f"Error getting top floors: {e}")
        return {}


def get_collection_floor(auth_data: str, collection_name: str):
    """Get floor price for collection by name (in TON) from sticker-sets."""
    try:
        collections = get_sticker_collections(auth_data)
        for c in collections:
            if c.get('title', '').lower() == collection_name.lower():
                return nano_to_ton(c['floorPriceNanoTons'])
        return None
    except Exception as e:
        print(f"Error getting collection floor: {e}")
        return None


def get_collection_stats(auth_data: str, collection_name: str, max_pages: int = 10):
    """Get collection stats: min/max/avg/median price, count on sale."""
    cursor = ""
    prices = []
    count_on_sale = 0
    page = 0

    try:
        while page < max_pages:
            resp = search_gifts(auth_data, collection_names=[collection_name], count=20, cursor=cursor)
            gifts_list = resp.get('gifts', [])

            if not gifts_list:
                break

            for gift in gifts_list:
                if gift.get('isOnSale'):
                    price = gift.get('salePrice', 0)
                    prices.append(price)
                    count_on_sale += 1

            cursor = resp.get('cursor', '')
            if not cursor:
                break

            page += 1
    except Exception as e:
        print(f"Error getting stats: {e}")

    if not prices:
        return {"error": f"Collection '{collection_name}' not found or no items for sale"}

    prices.sort()
    total = sum(prices)
    avg = total / len(prices)
    median = prices[len(prices) // 2]

    return {
        "collection": collection_name,
        "count_on_sale": count_on_sale,
        "floor_ton": nano_to_ton(prices[0]),
        "ceil_ton": nano_to_ton(prices[-1]),
        "avg_ton": nano_to_ton(int(avg)),
        "median_ton": nano_to_ton(median),
        "total_items_scanned": len(prices),
    }


def monitor_floors(auth_data: str, collections: list, interval_sec: int = 300,
                   duration_sec: int = 3600, log_file: str = "floor_monitor.json"):
    """Monitor collection floors with periodic checks and logging."""
    start_time = time.time()
    previous_floors = {}
    log_data = []

    print(f"📊 Monitoring {len(collections)} collections every {interval_sec}sec...")

    try:
        while True:
            elapsed = time.time() - start_time
            if duration_sec > 0 and elapsed > duration_sec:
                print(f"✅ Monitoring complete ({elapsed:.0f}sec)")
                break

            current_time = datetime.now().isoformat()
            current_floors = {}

            for coll in collections:
                try:
                    stats = get_collection_stats(auth_data, coll, max_pages=2)
                    if 'error' not in stats:
                        floor = stats['floor_ton']
                        current_floors[coll] = floor

                        if coll in previous_floors:
                            prev = previous_floors[coll]
                            change = floor - prev
                            change_pct = (change / prev * 100) if prev > 0 else 0
                            status = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                            print(f"{status} {coll}: {floor:.6f} TON ({change:+.6f}, {change_pct:+.2f}%)")

                            log_data.append({
                                "timestamp": current_time,
                                "collection": coll,
                                "floor_ton": floor,
                                "change_ton": change,
                                "change_pct": change_pct
                            })
                except Exception as e:
                    print(f"❌ Error {coll}: {e}")

            previous_floors = current_floors

            if log_data:
                try:
                    with open(log_file, 'w', encoding='utf-8') as f:
                        json.dump(log_data, f, indent=2, ensure_ascii=False)
                except IOError as e:
                    print(f"Error saving log: {e}")

            if duration_sec > 0:
                remaining = duration_sec - elapsed
                if remaining > 0:
                    print(f"⏳ Next check in {interval_sec}sec (remaining {remaining:.0f}sec)\n")
                    time.sleep(interval_sec)
            else:
                print(f"⏳ Next check in {interval_sec}sec\n")
                time.sleep(interval_sec)

    except KeyboardInterrupt:
        print("\n⛔ Monitoring stopped by user")

    print(f"📊 Logs saved to {log_file}")
    return log_data


def export_to_csv(auth_data: str, filename: str = "gifts.csv", collection: str = None, max_items: int = 1000):
    """Export gifts to CSV file."""
    cursor = ""
    gifts_data = []
    count = 0
    page = 0

    print(f"📥 Exporting gifts to {filename}...")

    try:
        while count < max_items:
            resp = search_gifts(auth_data, collection_names=[collection] if collection else [],
                               count=20, cursor=cursor)
            gifts_list = resp.get('gifts', [])

            if not gifts_list:
                break

            for gift in gifts_list:
                gifts_data.append({
                    'name': gift.get('name', ''),
                    'number': gift.get('number', ''),
                    'collection': gift.get('collectionTitle', ''),
                    'model': gift.get('modelTitle', ''),
                    'backdrop': gift.get('backdropName', ''),
                    'symbol': gift.get('symbolName', ''),
                    'is_on_sale': gift.get('isOnSale', False),
                    'price_ton': nano_to_ton(gift.get('salePrice', 0)) if gift.get('isOnSale') else '',
                    'model_rarity': gift.get('modelRarityPerMille', ''),
                    'backdrop_rarity': gift.get('backdropRarityPerMille', ''),
                    'symbol_rarity': gift.get('symbolRarityPerMille', ''),
                    'is_mine': gift.get('isMine', False),
                    'gift_type': gift.get('giftType', ''),
                })
                count += 1
                if count >= max_items:
                    break

            cursor = resp.get('cursor', '')
            if not cursor:
                break

            page += 1
            print(f"  Page {page}: loaded {count} gifts...")

        if gifts_data:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=gifts_data[0].keys())
                writer.writeheader()
                writer.writerows(gifts_data)
            print(f"✅ Exported {len(gifts_data)} gifts to {filename}")
        else:
            print("❌ No gifts to export")

    except Exception as e:
        print(f"Error exporting: {e}")

    return gifts_data


def export_collection_floors(auth_data: str, filename: str = "floors.csv", max_pages: int = 10):
    """Export floor prices for all collections to CSV."""
    print(f"📊 Exporting floors to {filename}...")

    try:
        floors = get_collection_floors_from_saling(auth_data, max_pages=max_pages)

        if not floors:
            print("❌ No floors data to export")
            return

        sorted_floors = sorted(floors.items(), key=lambda x: x[1])

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['collection_name', 'floor_ton', 'floor_nano'])
            for coll, price_ton in sorted_floors:
                price_nano = int(price_ton * 1_000_000_000)
                writer.writerow([coll, f"{price_ton:.9f}", price_nano])

        print(f"✅ Exported {len(floors)} collections to {filename}")
        return floors

    except Exception as e:
        print(f"Error exporting floors: {e}")
        return None


def parse_collection_full(auth_data: str, collection_name: str, max_pages: int = 100):
    """Parse full collection - all gifts for sale with detailed info."""
    cursor = ""
    all_gifts = []
    page = 0

    print(f"🔍 Parsing collection '{collection_name}'...")

    try:
        while page < max_pages:
            resp = search_gifts(auth_data, collection_names=[collection_name], count=20, cursor=cursor)
            gifts_list = resp.get('gifts', [])

            if not gifts_list:
                break

            for gift in gifts_list:
                if gift.get('isOnSale'):
                    gift_data = {
                        'name': gift.get('name', ''),
                        'number': gift.get('number', ''),
                        'title': gift.get('title', ''),
                        'model': gift.get('modelTitle', ''),
                        'backdrop': gift.get('backdropName', ''),
                        'symbol': gift.get('symbolName', ''),
                        'price_ton': nano_to_ton(gift.get('salePrice', 0)),
                        'price_nano': gift.get('salePrice', 0),
                        'model_rarity': gift.get('modelRarityPerMille', 0),
                        'backdrop_rarity': gift.get('backdropRarityPerMille', 0),
                        'symbol_rarity': gift.get('symbolRarityPerMille', 0),
                        'total_rarity': (
                            gift.get('modelRarityPerMille', 0) +
                            gift.get('backdropRarityPerMille', 0) +
                            gift.get('symbolRarityPerMille', 0)
                        ),
                        'gift_type': gift.get('giftType', ''),
                        'id': gift.get('id', '')
                    }
                    all_gifts.append(gift_data)

            cursor = resp.get('cursor', '')
            if not cursor:
                break

            page += 1
            print(f"  Page {page}: loaded {len(all_gifts)} gifts...")

        print(f"✅ Total gifts for sale: {len(all_gifts)}\n")

        if all_gifts:
            print(f"📊 FULL PARSE: {collection_name}")
            print("=" * 140)
            print(f"{'Name':<25} {'Model':<20} {'Backdrop':<20} {'Symbol':<15} {'Price (TON)':<15} {'Rarity':<12} {'Type':<12}")
            print("=" * 140)

            for gift in all_gifts[:50]:
                print(f"{gift['name']:<25} {gift['model']:<20} {gift['backdrop']:<20} {gift['symbol']:<15} "
                      f"{gift['price_ton']:<15.9f} {gift['total_rarity']:<12} {gift['gift_type']:<12}")

            if len(all_gifts) > 50:
                print(f"\n... and {len(all_gifts) - 50} more gifts")

            print("=" * 140)

    except Exception as e:
        print(f"Error parsing collection: {e}")

    return all_gifts
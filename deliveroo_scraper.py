import csv
import json

import requests
from bs4 import BeautifulSoup

API_KEY = 'AIzaSyBOVwxUM9akvFrSWmmb2iKc7Fe0vjRBY7c'
base_url = 'https://deliveroo.fr'
pid = 1
scraped_links = []

headers = {
    'authority': 'maps.googleapis.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'en-US,en;q=0.9,ur;q=0.8,mt;q=0.7,fr;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36',
    'x-client-data': 'CKO1yQEIjrbJAQiktskBCMG2yQEIqZ3KAQia28oBCJKhywEI2+/LAQie+csBCOaEzAEI3qnMAQj4qswBCIOrzAEI66vMAQjDrMwBGKupygE=',
}


def scrape(task_id, product_id, product_position, url):
    print(f'task: {task_id}, restaurant: {product_id}, position: {product_position}, link: {url}')
    name = category = score = ratings = minimum_price = delivery_price = descr = lat = lon = address = zipcode = secondary_phone = primary_phone = image = 'None'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    try:
        name_tag = soup.find('h1',
                             'ccl-2a4b5924e2237093 ccl-21bead492ce4ada2 ccl-9ff886da4b0592ae ccl-3fa5b2e17742d58a')
        if name_tag:
            name = name_tag.text.strip()
        spans = soup.findAll('span', 'ccl-19882374e640f487 ccl-1daa0367dee37c3b ccl-dfaaa1af6c70149c')
        for s in spans:
            if "(" and ")" in str(s):
                ratings = s.text.strip().replace('(', '').replace(')', '')
            if " km" and "À" in str(s):
                dist = s.text.strip().replace('À', '').replace('km', '').strip()
            if "€ de livraison" in str(s):
                delivery_price = s.text.strip().replace(' € de livraison', '').replace(',', '.')
            if "€ minimum" in str(s):
                minimum_price = s.text.strip().replace(' € minimum', '').replace(',', '.')
        span_score = soup.find("span", ["ccl-19882374e640f487 ccl-417df52a76832172 ccl-b308a2db3758e3e5",
                                        "ccl-19882374e640f487 ccl-1daa0367dee37c3b ccl-77427c4c077ca1ab"])
        if span_score:
            score = span_score.text.strip()
            if score.split(' '):
                score = score.split(' ')[0].strip()

        json_data = soup.find('script', id='__NEXT_DATA__').text
        location = json_data.split('{"pins":[{"')
        if len(location) > 1:
            locs = location[1]
            if locs:
                locsplit = locs.split('}]},"lines"')[0]
                if locsplit:
                    locsplitagain = locsplit.split(',')
                    if locsplitagain:
                        lat = locsplitagain[0].replace('lat":', '')
                        lon = locsplitagain[1].replace('"lon":', '')
        jd = json.loads(json_data)
        props = jd.get('props')
        if props:
            initial_state = props.get('initialState')
            if initial_state:
                menu_page = initial_state.get('menuPage')
                if menu_page:
                    menu = menu_page.get('menu')
                    if menu:
                        layout_groups = menu.get('layoutGroups')
                        for l in layout_groups:
                            if l.get('id') == 'info-modal':
                                descr = l.get('subheader')
                                if descr:
                                    descr = descr.strip()
                                layouts = l.get('layouts')
                                for layout in layouts:
                                    if layout.get('actionId') == 'layout-list-allergens':
                                        blocks = layout.get('blocks')
                                        action = blocks[0].get('actions')
                                        params = action[0].get('target').get('params')
                                        primary_phone = params[0].get('value')[0].strip()

                        meta = menu.get('meta')
                        if meta:
                            restaurant = meta.get('restaurant')
                            if restaurant:
                                res_loc = restaurant.get('location')
                                if res_loc:
                                    addr = res_loc.get('address')
                                    if addr:
                                        address = addr.get('address1')
                                        if address:
                                            zipcode = address.split(',')[-1].strip()
                            items = meta.get('items')
                            if items:
                                get_items(items, product_id)

                        head = menu.get('header')
                        if head:
                            img = head.get('image')
                            if img:
                                image = img.get('url')
                            hd_tags = head.get('headerTags')
                            if hd_tags:
                                lines = hd_tags.get('lines')
                                if len(lines) > 1:
                                    span_cats = lines[0].get('spans')
                                    cat = []
                                    for scat in span_cats:
                                        text_c = scat.get('text')
                                        if text_c is not None and '·' not in str(text_c):
                                            cat.append(text_c)
                                    category = ','.join([x.strip() for x in cat])
                                if score == 'None':
                                    for ls in lines:
                                        if "STAR_FILL" in str(ls):
                                            span_scr = ls.get('spans')
                                            if span_scr:
                                                score = span_scr[2].get('text').strip()
                                                if score.split(' '):
                                                    score = score.split(' ')[0].strip()
    except Exception as e:
        print(e)
        getjson = response.text.split('data-dom-id="app-element" type="application/json">')[1].split("</script>")[0]
        jd = json.loads(getjson)
        rates = jd.get("rating", {})
        if rates:
            score = rates.get("value", "")
            ratings = rates.get("formatted_count", "")
        restaurant = jd.get("restaurant")
        if restaurant:
            name = restaurant["name_with_branch"]
            street = restaurant["street_address"]
            zipcode = restaurant["post_code"]
            phone_numbers = restaurant["phone_numbers"]
            primary_phone = phone_numbers.get("primary")
            secondary_phone = phone_numbers.get("secondary")
            city = restaurant["city"]
            address = street + city + ',' + zipcode
            image = restaurant["image"]
            menu = restaurant.get('menu')
            if menu:
                menu_tags = menu.get('menu_tags')
                cat = []
                for m in menu_tags:
                    if m['type'] != "Collection":
                        cat.append(m['name'])
                category = ", ".join(cat)
        main_menu = jd.get('menu')
        if main_menu:
            items = main_menu.get('items')
            if items:
                get_items(items, product_id, False)

    out = [product_id, task_id, response.url, product_position, name, category, score, ratings, minimum_price,
           delivery_price,
           descr, lat,
           lon,
           address,
           zipcode, primary_phone, secondary_phone, image]
    # print(out)
    writer.writerow(out)


menu_id = 1


def get_items(items, restaurant_id, main=True):
    global menu_id
    for item in items:
        price = image = 'None'
        internal_id = item.get('id')
        name = item.get('name')
        descri = item.get('description')
        available = item.get('available')
        popular = item.get('popular')
        if main:
            category_id = item.get('categoryId')
            product_information = item.get('productInformation')
            nutritional_info = item.get('nutritionalInfo')
            pri = item.get('price')
            if pri:
                price = pri.get('formatted').split(' ')[0].replace(',', '.').replace("\xa0€", '').strip()
            price_discounted = item.get('priceDiscounted')
            if price_discounted:
                price_discounted = price_discounted.get('formatted').split(' ')[0].replace(',', '.').replace("\xa0€",
                                                                                                             '').strip()
            percentage_discounted = item.get('percentageDiscounted')
            img = item.get('image')
            if img:
                image = img.get('url')
            max_selection = item.get('maxSelection')
            is_signature_exclusive = item.get('isSignatureExclusive')
        else:
            max_selection = nutritional_info = percentage_discounted = 'null'
            category_id = item.get('category_id')
            product_information = item.get('product_information')
            price = item.get('raw_price')
            price_discounted = item.get('discounted_price')
            if price_discounted:
                if price_discounted.split(' '):
                    price_discounted = price_discounted[0].replace(',', '.').replace("\xa0€", '').strip()
            image = item.get('image')
            is_signature_exclusive = item.get('is_signature_exclusive')

        out_row = [menu_id, restaurant_id, internal_id, category_id, name, descri, product_information,
                   nutritional_info, price,
                   price_discounted,
                   percentage_discounted, image, popular, available, max_selection, is_signature_exclusive]
        menu_writer.writerow(out_row)
        menu_id += 1


def get_restaurants(url):
    global pid
    print("fetching restaurants: ", url)
    resp = requests.get(url)
    jd = json.loads(resp.text.split(' type="application/json">')[1].split('</script>')[0])
    state = jd["props"]["initialState"]["home"]['feed']['results']['data']
    total = 0
    pos = 1
    for row in state:
        blocks = row['blocks']
        for block in blocks:
            restaurant = block['target'].get('restaurant')
            if restaurant:
                rest_link = base_url + restaurant['links']['self']['href']
                if rest_link not in scraped_links:
                    try:
                        scrape(tid, pid, pos, rest_link)
                    except:
                        err.write(f'{tid},{pid},{pos},{rest_link}\n')
                    scraped_links.append(rest_link)
                    pid += 1
                pos += 1
                total += 1
    print("total:", total)
    wr.writerow([tid, postal, url, total])


def crawl_restaurants(place_id, formatted_address, lat, lng):
    site_headers = {
        "Accept-Language": "fr",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36 (deliveroo/consumer-web-app; browser)",
        "content-type": "application/json",
        "accept": "application/json, application/vnd.api+json"
    }
    cookies = {
        'roo_guid': '331ac57f-1329-4dd1-b84f-104738f2e83d',
        '_scid': 'c2b7a32d-7f94-4c44-a586-63c6306c3a92',
        '__stripe_mid': '22a4d0b9-2f0d-45fd-976e-9cbe926af67af1b30a',
        'OptanonAlertBoxClosed': '2022-05-05T10:19:39.040Z',
        '_gcl_au': '1.1.2082322627.1651745979',
        '_ga': 'GA1.1.966036796.1651745961',
        '_pin_unauth': 'dWlkPU1tRXlOVFpsTkRZdE9HUTJZeTAwTkdRMkxUa3lZbUl0TkRBNFpUQTNOVE0zWWpNNQ',
        'cikneeto_uuid': 'id:a2a680e7-6c54-430a-b6eb-b8bcbfffd306',
        '_tt_enable_cookie': '1',
        '_ttp': '10b0218a-d53e-4f95-8076-314c7e21e01c',
        'seen_cookie_message': 't',
        'has_dismissed_mobile_banner': 'false',
        '_sctr': '1|1652295600000',
        'location_data': 'eyJsb2NhdGlvbiI6eyJjb29yZGluYXRlcyI6WzMuODg5ODI1NCw0My41OTQwNjIzXSwiaWQiOm51bGwsImZvcm1hdHRlZF9hZGRyZXNzIjoiMTQwMCBDaGVtLiBkZSBNb3VsYXJlcywgMzQwMDAgTW9udHBlbGxpZXIsIEZyYW5jZSIsInBsYWNlX2lkIjoiQ2hJSmg5UTZhcFN2dGhJUk1XWTVkTGZoMXdvIiwicGluX3JlZmluZWQiOmZhbHNlLCJjaXR5IjpudWxsfX0.',
        'cwa_user_preferences': '{%22seen_modals%22:{%22nc_promos_nux_7719c5e8-372c-417f-9e77-e6774b905018%22:{%22id%22:%22nc_promos_nux_7719c5e8-372c-417f-9e77-e6774b905018%22%2C%22timestamp%22:1651746106}%2C%22nc_promos_nux_880c5b1e-04e9-4580-88a5-86907b3e0b4c%22:{%22id%22:%22nc_promos_nux_880c5b1e-04e9-4580-88a5-86907b3e0b4c%22%2C%22timestamp%22:1651987244}%2C%22nc_promos_voucher_bonapp7%22:{%22id%22:%22nc_promos_voucher_bonapp7%22%2C%22timestamp%22:1652178921}%2C%22nc_promos_voucher_7bonapp%22:{%22id%22:%22nc_promos_voucher_7bonapp%22%2C%22timestamp%22:1652540582}}}',
        'checkout_v2': '1',
        'roo_session_guid': 'f913544f-f8e1-4408-8590-369e35ad2218',
        'locale': 'eyJsb2NhbGUiOiJmciJ9',
        '__cf_bm': 'WYReVFX4gQ8nmeUraS0Z5sLBa_9kIMbOvhA0Pe1w4aI-1652596275-0-ATQ4oFYbUcBlqzzLsZSuP6qcRbqLffu9gOvHMqK9BQM40g9uFkt/vb14SNaTGs1o6e+NhjrO8P1+mWOHqZh2ZcrQ+tZQX8ZEvYkPl31McAIz',
        'roo_super_properties': 'eyJjb250ZXh0Ijp7InVzZXJBZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMDEuMC40OTUxLjY3IFNhZmFyaS81MzcuMzYiLCJpcCI6IjE4Mi4xNzcuMjM0LjI0MCIsImxvY2F0aW9uIjp7ImNvdW50cnkiOiJGcmFuY2UifSwibG9jYWxlIjoiZnIiLCJjYW1wYWlnbiI6eyJuYW1lIjoiZGlyZWN0Iiwic291cmNlIjoiZGlyZWN0IiwibWVkaXVtIjoibm9uZSJ9fSwiUmVxdWVzdGVkIExvY2FsZSI6ImVuIiwiUm9vQnJvd3NlciI6IkNocm9tZSIsIlJvb0Jyb3dzZXJWZXJzaW9uIjoiMTAxIiwiRGV2aWNlIFR5cGUiOiJkZXNrdG9wIiwiVExEIjoiZnIiLCJQbGF0Zm9ybSI6IndlYiIsIkxvY2FsZSI6ImZyIiwid2hpdGVfbGFiZWxfYnJhbmQiOiJjb3JlIn0.',
        '_clck': '136rv38|1|f1h|0',
        '_ga_ZW8Q7SZ57X': 'GS1.1.1652596278.10.1.1652596813.60',
        'C360i': '290A2FAB2DD0A92F1BF9F2D6680C8BEF|eyJjcmVhdGVkIjoxNjUxNzQ1OTQ5OTc4LCJ1cGRhdGVkIjoxNjUyNTk2ODE1NjQ3LCJ0YWdfaWQiOiI0LjMuMCIsImNvdW50Ijo0NSwiZXhwIjoxNjgzMjgxOTQ5OTc5fQ==',
        '_uetsid': '94964a00d39611ec8f2bbf75205c2b49',
        '_uetvid': '7a6a89b067e411ec827b590c26257ed3',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Sun+May+15+2022+11%3A40%3A16+GMT%2B0500+(Pakistan+Standard+Time)&version=6.27.0&isIABGlobal=false&consentId=0ec5ca38-a8eb-403e-91e9-a56fd53c7487&interactionCount=2&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&hosts=H46%3A1%2CH2%3A1%2CH37%3A1%2CH49%3A1%2CH24%3A1%2CH35%3A1%2CH38%3A1%2CH21%3A1%2CH23%3A1%2CH55%3A1%2CH39%3A1%2CH42%3A1%2CH4%3A1%2CH7%3A1%2CH3%3A1%2CH22%3A1%2CH6%3A1%2CH25%3A1%2CH26%3A1%2CH20%3A1%2CH11%3A1%2CH10%3A1%2CH17%3A1%2CH9%3A1%2CH19%3A1&AwaitingReconsent=false&genVendors=&geolocation=PK%3BPB',
        '_derived_epik': 'dj0yJnU9R01MRjhMbDZJUXBNUUhobHJ5eHJIQ2hIb0t4Q1hhc0Imbj1UYUpTakRuYWUxNGFGc0RieGZ2SlV3Jm09MSZ0PUFBQUFBR0tBb0ZFJnJtPTEmcnQ9QUFBQUFHS0FvRkU',
        '_clsk': 'my3pom|1652596818640|2|1|f.clarity.ms/collect',
        'cikneeto': 'date:1652596860166',
    }
    json_data = {"location": {"place_id": place_id, "formatted_address": formatted_address,
                              "coordinates": [lng, lat], "lat": lat, "lng": lng,
                              "pin_refined": False}}

    resp = requests.post("https://deliveroo.fr/api/restaurants", headers=site_headers, cookies=cookies, json=json_data)
    # print(resp)
    jd = resp.json()
    # print(jd)
    url = jd.get('url')
    if url:
        restaurants_link = base_url + url + "&collection=all-restaurants"
        get_restaurants(restaurants_link)
    else:
        wr.writerow([tid, postal, url, 0])


def get_location_data(tid, postal_input):
    print(f"[{tid}] Crawling: {postal_input}")
    args = {
        # 'address':postal_input,
        'key': API_KEY,
        'components': f'country:fr|postal_code:{postal_input}',
    }
    geocode_response = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=args,
                                    headers=headers)
    jd2 = geocode_response.json()
    # print(jd2)
    if 'error_message' in jd2:
        print(jd2.get('error_message'))
    results = jd2['results']
    if results:
        result = results[0]
        geometry = result['geometry']
        location = geometry['location']
        lat = location['lat']
        lng = location['lng']
        formatted_address = result['formatted_address']
        print(f'Address found: {formatted_address}')
        place_id = result['place_id']

        crawl_restaurants(place_id, formatted_address, lat, lng)
    else:
        wr.writerow([tid, postal_input, "", 0])


with open('inputs.csv') as inp, open("tasks.csv", 'w', encoding="utf-8", newline="") as tfile, open('restaurant.csv',
                                                                                                    'w',
                                                                                                    encoding='utf-8-sig',
                                                                                                    newline='') as f, open(
    'menu.csv', 'w',
    encoding='utf-8-sig',
    newline='') as d, open(
    'errors.txt', 'w') as err:
    writer = csv.writer(f)
    writer.writerow(
        ["result_id", "task_id", "url", "position", "name", "category", "score", "ratings", "minimum_price",
         "delivery_price", "description",
         "lat", "lng", "full_address", "zip_code", "phone_primary", "phone_secondary", "image_url"])
    menu_writer = csv.writer(d)
    menu_writer.writerow(["id", "result_id", "internal_id", "category_id", "name", "description", "product_information",
                          "nutritional_info", "price", "price_discounted", "percentage_discounted", "image_url",
                          "popular",
                          "available", "max_selection", "is_exclusive"])
    wr = csv.writer(tfile)
    wr.writerow(["id", "search_location", "url", "total_results"])

    all_post = []
    locations = [x.strip() for x in inp.readlines()]
    for loc in locations:
        sp = loc.split(',')
        tid = sp[0]
        postal = format(int(sp[1]), '05d')
        if postal not in all_post:
            all_post.append(postal)
            get_location_data(tid, postal)

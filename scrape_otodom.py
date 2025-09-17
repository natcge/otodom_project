# otodom_scraper.py
print("Script started")
from db import get_session, engine 
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

Base = declarative_base()

class Listing(Base):
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    district = Column(String)
    rooms = Column(Integer)
    area = Column(Float)
    seller_type = Column(String)

Base.metadata.create_all(engine)

print("After connecting to DB")

BASE_URL = "https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/wielkopolskie/poznan"
HEADLESS = True

async def process_listing(listing, session):
    # --- PRICE ---
    price_tag = listing.select_one('span[data-sentry-element="MainPrice"]')
    price = None
    if price_tag:
        price_text = price_tag.get_text(strip=True)
        price_clean = price_text.replace("\xa0", "").replace("zł", "").replace(" ", "").replace(",", ".")
        try:
            price = float(price_clean)
        except ValueError:
            pass

    # --- DISTRICT ---
    DISTRICTS = ["Stare Miasto", "Nowe Miasto", "Wilda", "Grunwald", "Jeżyce"]
    district = None
    address_tag = listing.select_one('p[data-sentry-component="Address"]')
    if address_tag:
        address = address_tag.get_text(strip=True)
        for d in DISTRICTS:
            if d.lower() in address.lower():
                district = d
                break

    # --- ROOMS ---
    rooms = None
    dt_tags = listing.find_all("dt")
    for dt in dt_tags:
        label = dt.get_text(strip=True)
        dd = dt.find_next_sibling("dd")
        if not dd:
            continue
        text = dd.get_text(strip=True)
        if "Liczba pokoi" in label:
            try:
                rooms = int(text.split()[0])
            except:
                pass

    # --- AREA ---
    area = None
    for dd in listing.find_all("dd"):
        span = dd.find("span")
        if span:
            text = span.get_text(strip=True)
            if "m²" in text:
                try:
                    area = float(text.replace("m²", "").replace(",", ".").strip())
                    break
                except ValueError:
                    continue

    # --- SELLER TYPE ---
    SELLER_TYPES = ["Deweloper", "Oferta prywatna", "Biuro nieruchomości"]
    seller_type = None

    # Try the precise/structured selectors first
    seller_span = listing.select_one(
        'span[data-sentry-element="OwnerType"][data-sentry-component="ConnectedOwnerType"]'
    ) or listing.select_one("span.css-n862hg.e1nndul84") or listing.select_one(
        'div[data-sentry-element="TextWrapper"] span'
    )

    # Fallback: scan common text containers for any of the known keywords
    if not seller_span:
        for tag in listing.select("span, div, p"):
            text = tag.get_text(" ", strip=True).replace("\xa0", " ")
            if any(st.lower() in text.lower() for st in SELLER_TYPES):
                seller_span = tag
                break

    # Extract canonical seller_type (match one of the known labels)
    if seller_span:
        text = seller_span.get_text(" ", strip=True).replace("\xa0", " ")
        for st in SELLER_TYPES:
            if st.lower() in text.lower():
                seller_type = st
                break


    # Save listing
    print(f"Extracted: price={price}, district={district}, rooms={rooms}, area={area}, seller_type={seller_type}")
    if district is not None:
        new_listing = Listing(
            price=price,
            district=district,
            rooms=rooms,
            area=area,
            seller_type=seller_type
        )
        session.add(new_listing)
    else:
        print("Skipping listing due to missing critical fields")

async def scrape_otodom(pages=10):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36")
        await page.set_extra_http_headers({
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.otodom.pl/"
        })

        session = get_session()
        print("dodo")
        DISTRICTS = ["Stare Miasto", "Nowe Miasto", "Wilda", "Grunwald", "Jeżyce"]
        try:
            for page_number in range(1, pages + 1):
                url = f"{BASE_URL}?strona={page_number}"
                await page.goto(url)
                await page.wait_for_timeout(3000)

                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                listings = soup.select('article')
                print(f"Page {page_number} - Found {len(listings)} listings")

                for listing in listings:
                    # Detect group listings and scrape them
                    group_footer = listing.select_one('div[data-sentry-element="MoreUnitsFooter"]')
                    if group_footer:
                        print("Detected group listing — opening full group page.")

                        try:
                            # Click the button instead of manually going to href
                            await page.click('a:has-text("Sprawdź wszystkie ogłoszenia")')

                            # Wait for the units section to appear
                            await page.wait_for_selector('#units-section', timeout=10000)

                            # Scroll to trigger lazy loading
                            for i in range(5):
                                await page.mouse.wheel(0, 1000)
                                await page.wait_for_timeout(1000)

                            # Extra wait for lazy content
                            await page.wait_for_timeout(2000)

                            # Now extract listings
                            group_html = await page.content()
                            group_soup = BeautifulSoup(group_html, 'html.parser')
                            unit_listings = group_soup.select('article')

                            print(f"Found {len(unit_listings)} listings inside group.")

                            for sub_listing in unit_listings:
                                # --- DISTRICT ---
                                district = None
                                title_loc = sub_listing.select_one('[data-sentry-element="TitleAndLocation"]')
                                if title_loc:
                                    location_text = title_loc.get_text(strip=True)
                                    for d in DISTRICTS:
                                        if d.lower() in location_text.lower():
                                            district = d
                                            break

                                # --- TABLE PARSING ---
                                area = None
                                rooms = None

                                table_labels = sub_listing.find_all("dt")
                                table_values = sub_listing.find_all("dd")

                                table_data = {dt.get_text(strip=True): dd.get_text(strip=True) for dt, dd in zip(table_labels, table_values)}

                                for key in table_data:
                                    if "Powierzchnia" in key:
                                        try:
                                            area = float(table_data[key].replace("m²", "").replace(",", ".").strip())
                                        except ValueError:
                                            pass
                                    elif "Pokoje" in key:
                                        try:
                                            rooms = int(table_data[key].split()[0])
                                        except ValueError:
                                            pass

                                # --- PRICE ---
                                price = None
                                price_tag = sub_listing.select_one('span[data-sentry-element="MainPrice"]')
                                if price_tag:
                                    price_text = price_tag.get_text(strip=True)
                                    price_clean = price_text.replace("\xa0", "").replace("zł", "").replace(" ", "").replace(",", ".")
                                    try:
                                        price = float(price_clean)
                                    except ValueError:
                                        pass

                                # --- SELLER TYPE ---
                                seller_type = "Deweloper"

                                print(f"[Group] Extracted: price={price}, district={district}, rooms={rooms}, area={area}, seller_type={seller_type}")
                                if district is not None:
                                    new_listing = Listing(
                                        price=price,
                                        district=district,
                                        rooms=rooms,
                                        area=area,
                                        seller_type=seller_type
                                    )
                                    session.add(new_listing)
                                else:
                                    print("[Group] Skipping listing due to missing critical fields")


                            await page.go_back()
                            await page.wait_for_timeout(2000)
                            continue  # Skip the original listing since we handled sub-units

                        except Exception as e:
                            print(f"Failed to process group listing: {e}")
                            await page.go_back()
                            await page.wait_for_timeout(2000)


                    # Process normal listing
                    await process_listing(listing, session)

                try:
                    session.commit()
                    print(f"Page {page_number} scraped and saved to DB")
                except Exception as e:
                    print("Commit failed:", e)
                    session.rollback()

        finally:
            session.close()

        await browser.close()

    print("Script finished")

if __name__ == "__main__":
    asyncio.run(scrape_otodom())

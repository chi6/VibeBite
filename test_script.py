import asyncio
from pyppeteer import launch

async def main(query):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(f'https://www.bing.com/search?form=QBRE&q={query}&cc=US')
    
    summaries = await page.evaluate('''() => {
        const liElements = Array.from(document.querySelectorAll("#b_results > .b_algo"));
        const firstFiveLiElements = liElements.slice(0, 5);
        return firstFiveLiElements.map(li => {
            const abstractElement = li.querySelector(".b_caption > p");
            const linkElement = li.querySelector("a");
            const href = linkElement.getAttribute("href");
            const title = linkElement.textContent;
            const abstract = abstractElement ? abstractElement.textContent : "";
            return { href, title, abstract };
        });
    }''')
    
    await browser.close()
    print(summaries)
    return summaries

# Example usage
asyncio.run(main("深圳美食"))
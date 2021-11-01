import csv
import json
from typing import List

import attr
from bs4 import BeautifulSoup as bs
from marshmallow import Schema, fields, post_load, EXCLUDE
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


@attr.s(auto_attribs=True, slots=True, frozen=True)
class CategoryItem:
    id: int = None
    title: str = None
    price: str = None
    available: str = None
    old_price: str = None
    link: str = None


class ProdSchema(Schema):
    id = fields.Str(default=None)
    title = fields.Str(default=None)
    price = fields.Dict(default=None)
    available = fields.Dict(default=None)
    old_price = fields.Field(default=None, allow_none=True)
    link = fields.Field(default=None)

    @post_load
    def create_prod(self, data, **kwargs):
        if isinstance(data['available'], dict):
            data['available'] = ', '.join(data['available']['offline']['region_iso_codes'])
        if isinstance(data['old_price'], dict):
            data['old_price'] = data['old_price']['price']
        return CategoryItem(**data)


def get_category_data(category_name: str) -> list:
    browser = webdriver.Chrome(ChromeDriverManager().install())

    browser.get(f'https://api.detmir.ru/v2/products?filter=categories[].alias:{category_name}&meta=*')
    soup = bs(browser.page_source, "html.parser")
    meta_data = soup.find('pre').text
    meta_data = json.loads(meta_data)
    total_prod_count = meta_data['meta']['length']

    browser.get(f'https://api.detmir.ru/v2/products?filter=categories[].alias:{category_name}&limit={total_prod_count}')
    soup = bs(browser.page_source, "html.parser")
    prods_html = soup.find('pre').text
    prods_data = json.loads(prods_html)

    return prods_data


def parse_data(input_data: List) -> List:
    parsed_data = []
    for item in input_data:
        if any(city in item['available']['offline']['region_iso_codes'] for city in ['RU-MOW', 'RU-SPE']):
            schema = ProdSchema(unknown=EXCLUDE)
            prod = schema.load(item)
            parsed_data.append(prod)
    return parsed_data


def write_data_to_csv(data: List) -> None:
    with open('result.csv', mode='w') as stream:
        col_names = ['id', 'name', 'price', 'city', 'old_price', 'url']
        writer = csv.DictWriter(stream, fieldnames=col_names)
        writer.writeheader()

        for item in data:
            writer.writerow({
                'id': item.id,
                'name': item.title,
                'price': item.price['price'],
                'city': item.available,
                'old_price': item.old_price,
                'url': item.link['web_url']
            })


if __name__ == '__main__':
    parsed_data = parse_data(get_category_data('lego'))
    write_data_to_csv(parsed_data)

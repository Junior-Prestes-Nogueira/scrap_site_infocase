# imports
import pandas as pd
from bs4 import BeautifulSoup
import requests
import re

# Determinando as categorias e o link por categoria
def get_url_categories():    
    url = "https://infosimples.github.io/ecommerce-example/"
    header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
    page = requests.get(url, headers=header).text
    soup = BeautifulSoup(page, 'html.parser')

    categories_search_tag =soup.find('ul', class_='breadcrumb').find_all('a')    

    categories_search_tag = soup.find('ul', class_='breadcrumb').find_all('a')

    url_categories = {categories.get_text(strip=True): "https://infosimples.github.io/" + categories.get('href') for categories in categories_search_tag}

    return url_categories


# Determinando numero maximo de pagina por categoria
def page_size_category(url_categories):
    page_size_category = {}
    
    for categorie, url in url_categories.items():    
        header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
        page = requests.get(url, headers=header).text
        soup = BeautifulSoup(page, 'html.parser')

        page_size_search_tag = soup.find('nav', class_='current-category').find('div', style= re.compile('padding.+')).get_text(strip=True)
        products_per_page = int(re.search('\d{2}', page_size_search_tag).group(0))
        max_number_of_products = int(re.search('of\s(\d.+)\s', page_size_search_tag).group(1))
        page_size = int(max_number_of_products / products_per_page) + 1

        page_size_category.update({url[:-1]: page_size})

    return page_size_category


# Acessando todas as paginas de todos os produtos e extraindo a url de todos os produtos ,e excluindo os repetidos:
def get_product_link_total_category(page_size_category):

    product_link_total_category = {}

    for url_base, max_page in page_size_category.items():

        product_link_list_total = []

        for index in range(1, max_page + 1):
            url = f'{url_base}{index}'

            header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
            page = requests.get(url, headers=header).text
            soup = BeautifulSoup(page, 'html.parser')

            # link do produto dentro da pagina
            product_link_search_tag = soup.find('div', class_='products-display').find_all('a', class_='product-card')
            products_link_list1 = ["https://infosimples.github.io" + product_link.get('href') for product_link in product_link_search_tag]
            product_link_list = pd.Series(products_link_list1).drop_duplicates().to_list()
            product_link_list_total += product_link_list

        # Determinando a categoria:        
        categorie = re.search('categories\/(.+)\/', url_base).group(1)

        product_link_total_category.update({categorie: product_link_list_total})
    
    return product_link_total_category


def get_df_final(product_link_total_category):
    # Extraindo os dados de todos os produtos do site:
    df_final = pd.DataFrame()
    for categorie, url_categorie_list in product_link_total_category.items():

        # Determinando produto por pagina
        df_products_category = pd.DataFrame()

        for url in url_categorie_list:

            df_all_subproducts = pd.DataFrame() # Para juntar todas as informacoes dos subprodutos por pagina de produto
            header = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"}
            page = requests.get(url, headers=header).text
            soup = BeautifulSoup(page, 'html.parser')
            product_container = soup.find_all('div', id=re.compile('product.+'))        

            for product in product_container:
                # id
                product_id = list(map(lambda x: x.get('id') if x else None, [product]))
                # name
                product_name = list(map(lambda x: x.find('meta', itemprop='name').get('content') if x.find('meta', itemprop='name') else None, [product]))
                # brand
                product_brand = list(map(lambda x: x.find('div', itemprop='brand').find('meta').get('content') if x.find('div', itemprop='brand') else None, [product]))
                # img link
                product_img_link= list(map(lambda x: x.find('link', itemprop='image').get('href') if x.find('link', itemprop='image') else None, [product]))
                # description
                product_description = list(map(lambda x: x.find('meta', itemprop='description').get('content') if x.find('meta', itemprop='description') else None, [product]))
                # available
                product_available = list(map(lambda x: True if bool(re.search('org\/(In)', x.find('meta', itemprop='availability', content=re.compile('Stock')).get('content'))) else False, [product]))[0]
                # sku-current-price
                product_current_price = list(map(lambda x: float(x.find('div', class_='sku-current-price').get_text(strip=True).replace('$', '')) if x.find('div', class_='sku-current-price') else None, [product]))
                # sku-old-price
                product_old_price = list(map(lambda x: float(x.find('div', class_='sku-old-price').get_text(strip=True).replace('$', '')) if x.find('div', class_='sku-old-price') else None, [product]))

                # product categorie:
                product_category = categorie                

                # product infos
                product_info = {'product_id': product_id, 'product_name': product_name, 'product_brand': product_brand, 'product_img_link': product_img_link,
                               'product_description': product_description, 'product_available': product_available, 'product_current_price': product_current_price, 
                                'product_old_price': product_old_price, 'product_category': product_category}

                df_subproduct = pd.DataFrame(product_info)
                df_all_subproducts = pd.concat([df_all_subproducts, df_subproduct], axis=0)    # todos subprodutos de uma pagina de produto


            df_products_category = pd.concat([df_products_category, df_all_subproducts])    # junção de todos os produtos de uma categoria inteira


        df_final = pd.concat([df_final, df_products_category])   

    return df_final


def save_to_json(df_final):
    df_final.drop_duplicates(subset='product_id', inplace=True)
    df_final = df_final.T
    df_final.columns = df_final.iloc[0]
    df_final.drop(index='product_id', inplace=True)
    df_final.to_json('json/products.json')

    return None
from scripts import info_case as workflow


if __name__ == '__main__':
    url_categories = workflow.get_url_categories()
    page_size_category = workflow.page_size_category(url_categories)
    product_link_total_category = workflow.get_product_link_total_category(page_size_category)
    df_final = workflow.get_df_final(product_link_total_category)
    workflow.save_to_json(df_final)
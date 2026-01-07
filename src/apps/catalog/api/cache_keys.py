def product_detail_cache_key(product_id: int | str) -> str:
    return f"catalog:product:{product_id}:detail:v1"
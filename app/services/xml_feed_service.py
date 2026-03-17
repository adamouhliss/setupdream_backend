from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from typing import List
from sqlalchemy.orm import Session, joinedload

from ..models.product import Product
from ..crud.product import CRUDProduct

product_crud = CRUDProduct()

class XMLFeedService:
    def __init__(self, base_url: str = "https://www.carresports.ma"):
        self.base_url = base_url.rstrip('/')
    
    def generate_product_feed(self, db: Session, include_inactive: bool = False) -> str:
        """
        Generate XML product feed with Google Shopping / Facebook format
        """
        # Create root RSS element
        rss = Element("rss")
        rss.set("version", "2.0")
        rss.set("xmlns:g", "http://base.google.com/ns/1.0")
        
        # Channel element
        channel = SubElement(rss, "channel")
        
        # Channel info
        SubElement(channel, "title").text = "Carré Sport - Équipements Sportifs Premium"
        SubElement(channel, "description").text = "Découvrez notre collection premium d'équipements sportifs au Maroc"
        SubElement(channel, "link").text = self.base_url
        
        # Get all active products
        products = self._get_products(db, include_inactive)
        
        # Add each product as an item
        for product in products:
            item = SubElement(channel, "item")
            self._add_product_to_feed(item, product)
        
        # Convert to pretty XML string
        rough_string = tostring(rss, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def generate_google_shopping_feed(self, db: Session) -> str:
        """
        Generate Google Shopping specific XML feed
        """
        # Create root RSS element with Google namespaces
        rss = Element("rss")
        rss.set("version", "2.0")
        rss.set("xmlns:g", "http://base.google.com/ns/1.0")
        
        channel = SubElement(rss, "channel")
        
        # Channel info
        SubElement(channel, "title").text = "Carré Sport - Google Shopping Feed"
        SubElement(channel, "description").text = "Produits Carré Sport pour Google Shopping"
        SubElement(channel, "link").text = self.base_url
        
        products = self._get_products(db)
        
        for product in products:
            item = SubElement(channel, "item")
            self._add_google_product_to_feed(item, product)
        
        rough_string = tostring(rss, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def generate_facebook_catalog_feed(self, db: Session) -> str:
        """
        Generate Facebook Catalog specific XML feed
        """
        rss = Element("rss")
        rss.set("version", "2.0")
        rss.set("xmlns:g", "http://base.google.com/ns/1.0")
        
        channel = SubElement(rss, "channel")
        
        SubElement(channel, "title").text = "Carré Sport - Facebook Catalog"
        SubElement(channel, "description").text = "Produits Carré Sport pour Facebook Shop"
        SubElement(channel, "link").text = self.base_url
        
        products = self._get_products(db)
        
        for product in products:
            item = SubElement(channel, "item")
            self._add_facebook_product_to_feed(item, product)
        
        rough_string = tostring(rss, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _get_products(self, db: Session, include_inactive: bool = False) -> List[Product]:
        """Get products with relationships loaded"""
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images)
        )
        
        if not include_inactive:
            query = query.filter(Product.is_active == True)
        
        return query.all()
    
    def _add_product_to_feed(self, item_element: Element, product: Product):
        """Add basic product information to feed"""
        # Generate SEO-friendly URL
        # Use stored slug if available, otherwise generate it
        slug = product.slug if product.slug else self._generate_product_slug(product)
        product_url = f"{self.base_url}/products/{slug}"
        
        # Required fields
        SubElement(item_element, "g:id").text = str(product.id)
        SubElement(item_element, "g:title").text = product.name
        SubElement(item_element, "g:description").text = self._clean_description(product.description or product.name)
        SubElement(item_element, "g:price").text = f"{product.sale_price or product.price:.2f} MAD"
        SubElement(item_element, "g:condition").text = "new"
        SubElement(item_element, "g:link").text = product_url
        SubElement(item_element, "g:availability").text = self._get_availability(product)
        SubElement(item_element, "g:image_link").text = self._get_image_url(product)
        
        # Additional useful fields
        if product.category:
            SubElement(item_element, "g:product_type").text = product.category.name
            SubElement(item_element, "g:google_product_category").text = self._get_google_category(product.category.name)
        
        if product.brand:
            SubElement(item_element, "g:brand").text = product.brand
            
        if product.sku:
            SubElement(item_element, "g:mpn").text = product.sku
            
        # Size and color variants
        if product.sizes and len(product.sizes) > 0:
            SubElement(item_element, "g:size").text = "/".join(product.sizes)
            
        if product.color:
            SubElement(item_element, "g:color").text = product.color
            
        # Sale price if applicable
        if product.sale_price and product.sale_price < product.price:
            SubElement(item_element, "g:sale_price").text = f"{product.sale_price:.2f} MAD"
            
        # Weight and shipping
        if product.weight:
            SubElement(item_element, "g:shipping_weight").text = f"{product.weight} kg"
            
        SubElement(item_element, "g:shipping").text = "MA:Standard:50 MAD"
        SubElement(item_element, "g:identifier_exists").text = "yes" if product.sku else "no"
    
    def _generate_product_slug(self, product: Product) -> str:
        """
        Generate SEO-friendly slug matching frontend logic:
        name + color + brand (if not in name) + id
        Fallback if slug is not in DB.
        """
        import unicodedata
        import re
        
        # Build base parts
        parts = [product.name]
        
        if product.color:
            parts.append(product.color)
            
        if product.brand and product.brand.lower() not in product.name.lower():
            parts.append(product.brand)
            
        text = " ".join(parts)
        
        # Custom replacements to match frontend slugUtils.ts exactly
        text = text.lower().strip()
        text = text.replace('à', 'a').replace('á', 'a').replace('â', 'a').replace('ã', 'a').replace('ä', 'a').replace('å', 'a')
        text = text.replace('è', 'e').replace('é', 'e').replace('ê', 'e').replace('ë', 'e')
        text = text.replace('ì', 'i').replace('í', 'i').replace('î', 'i').replace('ï', 'i')
        text = text.replace('ò', 'o').replace('ó', 'o').replace('ô', 'o').replace('õ', 'o').replace('ö', 'o')
        text = text.replace('ù', 'u').replace('ú', 'u').replace('û', 'u').replace('ü', 'u')
        text = text.replace('ý', 'y').replace('ÿ', 'y')
        text = text.replace('ñ', 'n')
        text = text.replace('ç', 'c')
        text = text.replace('ß', 'ss')
        text = text.replace('æ', 'ae')
        text = text.replace('œ', 'oe')
        
        # Remove remaining special chars (fallback for anything missed above)
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        
        # Replace non-alphanumeric characters with hyphens
        text = re.sub(r'[^a-z0-9]+', '-', text)
        
        # Remove leading/trailing hyphens and multiple consecutive hyphens
        text = text.strip('-')
        
        # Append ID to ensure uniqueness matches frontend logic
        return f"{text}-{product.id}"

    def _add_google_product_to_feed(self, item_element: Element, product: Product):
        """Add Google Shopping specific fields"""
        self._add_product_to_feed(item_element, product)
        
        # Google Shopping specific fields
        SubElement(item_element, "g:adult").text = "no"
        SubElement(item_element, "g:age_group").text = "adult"
        SubElement(item_element, "g:gender").text = "unisex"
        
        # Custom labels for campaign management
        if product.is_featured:
            SubElement(item_element, "g:custom_label_0").text = "featured"
            
        if product.category:
            SubElement(item_element, "g:custom_label_1").text = product.category.name.lower()
            
        # Promotion eligibility
        SubElement(item_element, "g:promotion_id").text = "FREE_SHIPPING_500MAD"
    
    def _add_facebook_product_to_feed(self, item_element: Element, product: Product):
        """Add Facebook Catalog specific fields"""
        self._add_product_to_feed(item_element, product)
        
        # Facebook specific fields
        SubElement(item_element, "g:fb_product_category").text = self._get_facebook_category(product.category.name if product.category else "")
        
        # Inventory
        if product.stock_quantity > 0:
            SubElement(item_element, "g:quantity_to_sell_on_facebook").text = str(min(product.stock_quantity, 999))
        
    def _clean_description(self, description: str) -> str:
        """Clean and format product description"""
        if not description:
            return "Équipement sportif de qualité premium chez Carré Sport"
        
        # Remove HTML tags if any
        import re
        clean_desc = re.sub(r'<[^>]+>', '', description)
        
        # Limit length (recommended max 5000 chars for Google)
        if len(clean_desc) > 1000:
            clean_desc = clean_desc[:997] + "..."
        
        return clean_desc.strip()
    
    def _get_availability(self, product: Product) -> str:
        """Get product availability status"""
        if product.stock_quantity <= 0:
            return "out of stock"
        elif product.stock_quantity <= product.low_stock_threshold:
            return "limited availability"
        else:
            return "in stock"
    
    def _get_image_url(self, product: Product) -> str:
        """Get product primary image URL"""
        if product.image_url:
            # Handle relative URLs
            if product.image_url.startswith('/'):
                return f"https://projects-backend.mlqyyh.easypanel.host{product.image_url}"
            elif product.image_url.startswith('http'):
                return product.image_url
            else:
                return f"https://projects-backend.mlqyyh.easypanel.host/uploads/products/{product.image_url}"
        
        # Fallback to default image
        return f"{self.base_url}/images/products/placeholder.jpg"
    
    def _get_google_category(self, category_name: str) -> str:
        """Map internal categories to Google product categories"""
        category_mapping = {
            "Equipment": "499676",  # Sporting Goods > Fitness & Exercise > Strength Training Equipment
            "Footwear": "187",      # Apparel & Accessories > Shoes
            "Clothing": "1604",     # Apparel & Accessories > Clothing > Activewear
            "Accessories": "499840", # Sporting Goods > Exercise & Fitness > Accessories
            "Training": "499676",   # Sporting Goods > Fitness & Exercise
        }
        return category_mapping.get(category_name, "499676")  # Default to fitness equipment
    
    def _get_facebook_category(self, category_name: str) -> str:
        """Map internal categories to Facebook product categories"""
        category_mapping = {
            "Equipment": "Health & Beauty > Personal Care > Fitness & Nutrition > Exercise Equipment",
            "Footwear": "Apparel & Accessories > Shoes > Athletic Shoes",
            "Clothing": "Apparel & Accessories > Clothing > Activewear",
            "Accessories": "Sporting Goods > Exercise & Fitness",
            "Training": "Sporting Goods > Exercise & Fitness",
        }
        return category_mapping.get(category_name, "Sporting Goods")

# Create service instance
xml_feed_service = XMLFeedService() 
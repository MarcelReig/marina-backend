"""
Cloudinary service for image management
"""

import cloudinary.uploader


class CloudinaryService:
    """Service for handling image uploads to Cloudinary"""
    
    @staticmethod
    def upload_image(image_data, folder="portfolio"):
        """Upload image data to Cloudinary and return URL
        
        Args:
            image_data (str): Base64 image data
            folder (str): Cloudinary folder name
            
        Returns:
            str or None: Secure URL if successful, None if failed
        """
        try:
            result = cloudinary.uploader.upload(
                image_data,
                folder=folder,
                resource_type="image"
            )
            return result['secure_url']
        except Exception as e:
            # Avoid noisy prints in production; caller handles the error
            return None
    
    @staticmethod
    def upload_portfolio_images(thumb_img_data, gallery_data):
        """Upload portfolio images (thumbnail + gallery)
        
        Args:
            thumb_img_data (str): Base64 thumbnail image
            gallery_data (list): List of base64 gallery images
            
        Returns:
            tuple: (thumb_url, gallery_urls, error_message)
        """
        try:
            # Upload thumbnail
            thumb_url = CloudinaryService.upload_image(thumb_img_data, "portfolio/thumbnails")
            if not thumb_url:
                return None, None, "Failed to upload thumbnail"
            
            # Upload gallery images
            gallery_urls = []
            for img_data in gallery_data:
                img_url = CloudinaryService.upload_image(img_data, "portfolio/gallery")
                if img_url:
                    gallery_urls.append(img_url)
                else:
                    return None, None, "Failed to upload gallery image"
            
            return thumb_url, gallery_urls, None
            
        except Exception as e:
            return None, None, f"Upload error: {str(e)}"
    
    @staticmethod
    def upload_store_image(image_data):
        """Upload store item image to Cloudinary
        
        Args:
            image_data (str): Base64 image data
            
        Returns:
            tuple: (image_url, error_message)
        """
        try:
            image_url = CloudinaryService.upload_image(image_data, "store/products")
            if not image_url:
                return None, "Failed to upload store image"
            
            return image_url, None
            
        except Exception as e:
            return None, f"Store image upload error: {str(e)}"

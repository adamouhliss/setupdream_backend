from typing import Any, Dict, Optional, List
from sqlalchemy.orm import Session

from ..models.settings import Settings
from ..schemas.settings import SettingsCreate, SettingsUpdate


class CRUDSettings:
    def get(self, db: Session, id: Any) -> Optional[Settings]:
        return db.query(Settings).filter(Settings.id == id).first()

    def get_by_category_and_key(self, db: Session, *, category: str, key: str) -> Optional[Settings]:
        return db.query(Settings).filter(
            Settings.category == category, Settings.key == key
        ).first()

    def get_by_category(self, db: Session, *, category: str) -> List[Settings]:
        return db.query(Settings).filter(Settings.category == category).all()

    def get_all_categories(self, db: Session) -> List[str]:
        """Get all unique categories"""
        result = db.query(Settings.category).distinct().all()
        return [row[0] for row in result]

    def create(self, db: Session, *, obj_in: SettingsCreate) -> Settings:
        db_obj = Settings(
            category=obj_in.category,
            key=obj_in.key,
            value=obj_in.value,
            data_type=obj_in.data_type
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Settings,
        obj_in: SettingsUpdate
    ) -> Settings:
        update_data = obj_in.dict(exclude_unset=True)
        
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def upsert_setting(self, db: Session, *, category: str, key: str, value: Any) -> Settings:
        """Create or update a setting"""
        setting = self.get_by_category_and_key(db, category=category, key=key)
        
        if setting:
            # Update existing setting
            setting.set_typed_value(value)
            db.add(setting)
        else:
            # Create new setting
            setting = Settings(category=category, key=key)
            setting.set_typed_value(value)
            db.add(setting)
        
        db.commit()
        db.refresh(setting)
        return setting

    def bulk_upsert_category(self, db: Session, *, category: str, settings_dict: Dict[str, Any]) -> List[Settings]:
        """Bulk create or update settings for a category"""
        results = []
        
        for key, value in settings_dict.items():
            setting = self.upsert_setting(db, category=category, key=key, value=value)
            results.append(setting)
        
        return results

    def get_category_as_dict(self, db: Session, *, category: str) -> Dict[str, Any]:
        """Get all settings for a category as a dictionary"""
        settings = self.get_by_category(db, category=category)
        result = {}
        
        for setting in settings:
            result[setting.key] = setting.get_typed_value()
        
        return result

    def delete(self, db: Session, *, id: int) -> Settings:
        obj = db.query(Settings).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def delete_by_category_and_key(self, db: Session, *, category: str, key: str) -> bool:
        setting = self.get_by_category_and_key(db, category=category, key=key)
        if setting:
            db.delete(setting)
            db.commit()
            return True
        return False

    def delete_category(self, db: Session, *, category: str) -> int:
        """Delete all settings for a category. Returns number of deleted settings."""
        count = db.query(Settings).filter(Settings.category == category).count()
        db.query(Settings).filter(Settings.category == category).delete()
        db.commit()
        return count


settings = CRUDSettings() 
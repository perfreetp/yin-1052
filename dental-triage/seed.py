from app.database import SessionLocal, engine, Base
from app.models import Clinic, Doctor, Lead, TriageRecord, Dispatch, ArrivalConfirmation

Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        if db.query(Clinic).first():
            print("已有数据，跳过种子")
            return

        c1 = Clinic(
            name="瑞尔齿科·国贸中心",
            address="北京市朝阳区建国门外大街1号国贸商城3层",
            latitude=39.9087,
            longitude=116.4605,
            phone="010-65051234",
            business_hours="周一至周日 09:00-18:00",
        )
        c2 = Clinic(
            name="瑞尔齿科·望京中心",
            address="北京市朝阳区望京街9号望京国际商业中心2层",
            latitude=39.9887,
            longitude=116.4754,
            phone="010-84701234",
            business_hours="周一至周日 09:00-18:00",
        )
        c3 = Clinic(
            name="瑞尔齿科·中关村中心",
            address="北京市海淀区中关村大街15号中关村广场1层",
            latitude=39.9812,
            longitude=116.3105,
            phone="010-82501234",
            business_hours="周一至周六 09:00-17:30",
        )
        db.add_all([c1, c2, c3])
        db.flush()

        doctors = [
            Doctor(name="张建国", clinic_id=c1.id, title="主任医师", specialties="种植,外科", available_slots=8),
            Doctor(name="李雅琴", clinic_id=c1.id, title="副主任医师", specialties="正畸", available_slots=5),
            Doctor(name="王瑞芳", clinic_id=c1.id, title="主治医师", specialties="修复,牙体牙髓", available_slots=12),
            Doctor(name="陈晓明", clinic_id=c1.id, title="主治医师", specialties="洁牙,牙周", available_slots=15),
            Doctor(name="刘婷婷", clinic_id=c1.id, title="主治医师", specialties="儿童齿科", available_slots=10),
            Doctor(name="赵伟", clinic_id=c2.id, title="主任医师", specialties="种植,修复", available_slots=6),
            Doctor(name="孙丽华", clinic_id=c2.id, title="副主任医师", specialties="正畸,儿童齿科", available_slots=7),
            Doctor(name="周敏", clinic_id=c2.id, title="主治医师", specialties="牙体牙髓,牙周", available_slots=11),
            Doctor(name="吴刚", clinic_id=c2.id, title="主治医师", specialties="洁牙", available_slots=20),
            Doctor(name="郑海燕", clinic_id=c3.id, title="主任医师", specialties="正畸,种植", available_slots=4),
            Doctor(name="钱峰", clinic_id=c3.id, title="副主任医师", specialties="修复", available_slots=9),
            Doctor(name="冯丽", clinic_id=c3.id, title="主治医师", specialties="儿童齿科,洁牙", available_slots=13),
        ]
        db.add_all(doctors)
        db.commit()
        print("种子数据已插入")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

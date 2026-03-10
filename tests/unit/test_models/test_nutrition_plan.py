"""营养计划模型测试"""

from datetime import date, timedelta
import pytest

from src.fatloss.calculator.nutrition_calculator import NutritionDistribution
from src.fatloss.models.nutrition_plan import DailyNutritionPlan, WeeklyNutritionPlan


class TestDailyNutritionPlan:
    """每日营养计划模型测试类"""

    def test_create_daily_nutrition_plan_minimal(self):
        """测试创建最小化每日营养计划"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
        )
        assert plan.id is None
        assert plan.user_id == 1
        assert plan.plan_date == date.today()
        assert plan.target_tdee == 2000.0
        assert plan.nutrition == nutrition
        assert plan.is_adjusted == False
        assert plan.adjustment_units == 0
        assert plan.notes == ""
        assert plan.created_at == date.today()

    def test_create_daily_nutrition_plan_full(self):
        """测试创建完整每日营养计划"""
        nutrition = NutritionDistribution(
            carbohydrates_g=250.0,
            protein_g=180.0,
            fat_g=60.0,
            total_calories=2500.0,
        )
        plan = DailyNutritionPlan(
            id=1,
            user_id=1,
            plan_date=date.today(),
            target_tdee=2200.0,
            nutrition=nutrition,
            is_adjusted=True,
            adjustment_units=2,
            notes="测试计划",
            created_at=date(2024, 1, 2),
        )
        assert plan.id == 1
        assert plan.user_id == 1
        assert plan.plan_date == date.today()
        assert plan.target_tdee == 2200.0
        assert plan.nutrition == nutrition
        assert plan.is_adjusted == True
        assert plan.adjustment_units == 2
        assert plan.notes == "测试计划"
        assert plan.created_at == date(2024, 1, 2)

    def test_plan_date_validation(self):
        """测试计划日期验证"""
        # 今天日期
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
        )
        assert plan.plan_date == date.today()
        
        # 未来日期
        future_date = date.today()
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=future_date,
            target_tdee=2000.0,
            nutrition=nutrition,
        )
        assert plan.plan_date == future_date
        
        # 过去日期应引发错误
        with pytest.raises(ValueError, match="计划日期不能是过去日期"):
            DailyNutritionPlan(
                user_id=1,
                plan_date=date(2020, 1, 1),
                target_tdee=2000.0,
                nutrition=nutrition,
            )

    def test_user_id_validation(self):
        """测试用户ID验证"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        # 有效用户ID
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
        )
        assert plan.user_id == 1
        
        # 零或负数应引发错误
        with pytest.raises(ValueError, match="greater than 0"):
            DailyNutritionPlan(
                user_id=0,
                plan_date=date.today(),
                target_tdee=2000.0,
                nutrition=nutrition,
            )
        
        with pytest.raises(ValueError, match="greater than 0"):
            DailyNutritionPlan(
                user_id=-1,
                plan_date=date.today(),
                target_tdee=2000.0,
                nutrition=nutrition,
            )

    def test_target_tdee_validation(self):
        """测试目标TDEE验证"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        # 正数
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=100.0,
            nutrition=nutrition,
        )
        assert plan.target_tdee == 100.0
        
        # 零或负数应引发错误
        with pytest.raises(ValueError, match="greater than 0"):
            DailyNutritionPlan(
                user_id=1,
                plan_date=date.today(),
                target_tdee=0.0,
                nutrition=nutrition,
            )
        
        with pytest.raises(ValueError, match="greater than 0"):
            DailyNutritionPlan(
                user_id=1,
                plan_date=date.today(),
                target_tdee=-100.0,
                nutrition=nutrition,
            )

    def test_notes_length_validation(self):
        """测试备注长度验证"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        # 正常备注
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
            notes="测试备注",
        )
        assert plan.notes == "测试备注"
        
        # 长备注
        long_notes = "x" * 500
        plan = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
            notes=long_notes,
        )
        assert plan.notes == long_notes
        
        # 超长备注应引发错误
        with pytest.raises(ValueError, match="at most 500 characters"):
            DailyNutritionPlan(
                user_id=1,
                plan_date=date.today(),
                target_tdee=2000.0,
                nutrition=nutrition,
                notes="x" * 501,
            )

    def test_json_serialization(self):
        """测试JSON序列化"""
        nutrition = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        plan = DailyNutritionPlan(
            id=1,
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition,
            is_adjusted=True,
            adjustment_units=2,
            notes="测试",
            created_at=date(2024, 1, 2),
        )
        
        json_data = plan.model_dump_json()
        today_str = date.today().isoformat()
        assert '"id":1' in json_data
        assert '"user_id":1' in json_data
        assert f'"plan_date":"{today_str}"' in json_data
        assert '"target_tdee":2000.0' in json_data
        assert '"is_adjusted":true' in json_data
        assert '"adjustment_units":2' in json_data
        assert '"notes":"测试"' in json_data
        assert '"created_at":"2024-01-02"' in json_data


class TestWeeklyNutritionPlan:
    """每周营养计划模型测试类"""

    def test_create_weekly_nutrition_plan_minimal(self):
        """测试创建最小化每周营养计划"""
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
        )
        assert plan.id is None
        assert plan.user_id == 1
        assert plan.week_start_date == date(2024, 1, 1)
        assert plan.week_end_date == date(2024, 1, 7)
        assert plan.daily_plans == []
        assert plan.total_carbohydrates_g == 1400.0
        assert plan.total_protein_g == 1050.0
        assert plan.total_fat_g == 350.0
        assert plan.notes == ""
        assert plan.created_at == date.today()

    def test_create_weekly_nutrition_plan_full(self):
        """测试创建完整每周营养计划"""
        plan = WeeklyNutritionPlan(
            id=1,
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            daily_plans=[],
            total_carbohydrates_g=1500.0,
            total_protein_g=1200.0,
            total_fat_g=400.0,
            notes="测试周计划",
            created_at=date(2024, 1, 8),
        )
        assert plan.id == 1
        assert plan.user_id == 1
        assert plan.week_start_date == date(2024, 1, 1)
        assert plan.week_end_date == date(2024, 1, 7)
        assert plan.daily_plans == []
        assert plan.total_carbohydrates_g == 1500.0
        assert plan.total_protein_g == 1200.0
        assert plan.total_fat_g == 400.0
        assert plan.notes == "测试周计划"
        assert plan.created_at == date(2024, 1, 8)

    def test_week_dates_validation(self):
        """测试周日期验证"""
        # 正常范围
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
        )
        assert plan.week_start_date == date(2024, 1, 1)
        assert plan.week_end_date == date(2024, 1, 7)
        
        # 结束日期等于开始日期应引发错误
        with pytest.raises(ValueError, match="周结束日期必须晚于周开始日期"):
            WeeklyNutritionPlan(
                user_id=1,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 1),
                total_carbohydrates_g=1400.0,
                total_protein_g=1050.0,
                total_fat_g=350.0,
            )
        
        # 结束日期早于开始日期应引发错误
        with pytest.raises(ValueError, match="周结束日期必须晚于周开始日期"):
            WeeklyNutritionPlan(
                user_id=1,
                week_start_date=date(2024, 1, 7),
                week_end_date=date(2024, 1, 1),
                total_carbohydrates_g=1400.0,
                total_protein_g=1050.0,
                total_fat_g=350.0,
            )

    def test_user_id_validation(self):
        """测试用户ID验证"""
        # 有效用户ID
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
        )
        assert plan.user_id == 1
        
        # 零或负数应引发错误
        with pytest.raises(ValueError, match="greater than 0"):
            WeeklyNutritionPlan(
                user_id=0,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                total_carbohydrates_g=1400.0,
                total_protein_g=1050.0,
                total_fat_g=350.0,
            )
        
        with pytest.raises(ValueError, match="greater than 0"):
            WeeklyNutritionPlan(
                user_id=-1,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                total_carbohydrates_g=1400.0,
                total_protein_g=1050.0,
                total_fat_g=350.0,
            )

    def test_nutrient_validation(self):
        """测试营养素验证"""
        # 正数
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=100.0,
            total_protein_g=50.0,
            total_fat_g=20.0,
        )
        assert plan.total_carbohydrates_g == 100.0
        assert plan.total_protein_g == 50.0
        assert plan.total_fat_g == 20.0
        
        # 零或负数应引发错误
        with pytest.raises(ValueError, match="greater than 0"):
            WeeklyNutritionPlan(
                user_id=1,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                total_carbohydrates_g=0.0,
                total_protein_g=50.0,
                total_fat_g=20.0,
            )
        
        with pytest.raises(ValueError, match="greater than 0"):
            WeeklyNutritionPlan(
                user_id=1,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                total_carbohydrates_g=-100.0,
                total_protein_g=50.0,
                total_fat_g=20.0,
            )

    def test_notes_length_validation(self):
        """测试备注长度验证"""
        # 正常备注
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
            notes="测试备注",
        )
        assert plan.notes == "测试备注"
        
        # 长备注
        long_notes = "x" * 1000
        plan = WeeklyNutritionPlan(
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
            notes=long_notes,
        )
        assert plan.notes == long_notes
        
        # 超长备注应引发错误
        with pytest.raises(ValueError, match="at most 1000 characters"):
            WeeklyNutritionPlan(
                user_id=1,
                week_start_date=date(2024, 1, 1),
                week_end_date=date(2024, 1, 7),
                total_carbohydrates_g=1400.0,
                total_protein_g=1050.0,
                total_fat_g=350.0,
                notes="x" * 1001,
            )

    def test_from_daily_plans(self):
        """测试从每日计划列表创建周计划"""
        nutrition1 = NutritionDistribution(
            carbohydrates_g=200.0,
            protein_g=150.0,
            fat_g=50.0,
            total_calories=2000.0,
        )
        nutrition2 = NutritionDistribution(
            carbohydrates_g=250.0,
            protein_g=180.0,
            fat_g=60.0,
            total_calories=2000.0,
        )
        
        daily_plan1 = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today(),
            target_tdee=2000.0,
            nutrition=nutrition1,
        )
        daily_plan2 = DailyNutritionPlan(
            user_id=1,
            plan_date=date.today() + timedelta(days=1),
            target_tdee=2200.0,
            nutrition=nutrition2,
        )
        
        weekly_plan = WeeklyNutritionPlan.from_daily_plans([daily_plan1, daily_plan2])
        
        assert weekly_plan.user_id == 1
        assert weekly_plan.week_start_date == date.today()
        assert weekly_plan.week_end_date == date.today() + timedelta(days=1)
        assert weekly_plan.daily_plans == [daily_plan1, daily_plan2]
        assert weekly_plan.total_carbohydrates_g == 450.0  # 200 + 250
        assert weekly_plan.total_protein_g == 330.0  # 150 + 180
        assert weekly_plan.total_fat_g == 110.0  # 50 + 60
        assert weekly_plan.notes == ""

    def test_from_daily_plans_empty_list(self):
        """测试从空列表创建周计划应引发错误"""
        with pytest.raises(ValueError, match="每日计划列表不能为空"):
            WeeklyNutritionPlan.from_daily_plans([])

    def test_json_serialization(self):
        """测试JSON序列化"""
        plan = WeeklyNutritionPlan(
            id=1,
            user_id=1,
            week_start_date=date(2024, 1, 1),
            week_end_date=date(2024, 1, 7),
            total_carbohydrates_g=1400.0,
            total_protein_g=1050.0,
            total_fat_g=350.0,
            notes="测试",
            created_at=date(2024, 1, 8),
        )
        
        json_data = plan.model_dump_json()
        assert '"id":1' in json_data
        assert '"user_id":1' in json_data
        assert '"week_start_date":"2024-01-01"' in json_data
        assert '"week_end_date":"2024-01-07"' in json_data
        assert '"total_carbohydrates_g":1400.0' in json_data
        assert '"total_protein_g":1050.0' in json_data
        assert '"total_fat_g":350.0' in json_data
        assert '"notes":"测试"' in json_data
        assert '"created_at":"2024-01-08"' in json_data
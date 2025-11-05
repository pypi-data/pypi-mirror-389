from .main_app import CreatePromotionFile
from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_version() -> str:
    now = datetime.now()+ relativedelta(months=1)
    month = f"{now.month:02d}"
    year = str(now.year)
    version_code = f"{year[-2:]}0{month}"
    return version_code
def main():
    CreatePromotion = CreatePromotionFile(load=True,sub_sheet=True)
    version :str = get_version()
    CreatePromotion._set_version(version)
    CreatePromotion.start()


if __name__ == "__main__":
    main()

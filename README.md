# 꼭 읽어주세요

## 개요
특정 다음 카페, 특정 게시판에 들어가서 게시자, 게시일자, 제목, 조회수 등의 정보와 함께
스크린샷을 저장해주는 프로그램입니다

## 개발환경
* Windows 10
* PowerShell
* Python 3.6.1
* Virtualenv
* Firefox
* Selenium 3.4.3
* Git

## Dependencies
```
openpyxl==2.4.8
Pillow==4.2.0
pypiwin32==220
selenium==3.4.3
```

## 설치
> Windows 10 기준으로 명령어를 적었습니다

**PowerShell 관리자 권한으로 실행**
```
(Virtualenv등의 스크립트를 실행시키기 위한 PowerShell 설정)
> Set-ExecutionPolicy RemoteSigned

> cd path/to/your/workspace
> git clone https://github.com/DevSusu/DaumCafeCrawler
> cd DaumCafeCrawler
> mkdir screenshot

(Python version should be 3)
> virtualenv env_name_you_want
> env_name_you_want/Scripts/activate

> pip install -r requirements.txt
```

Firefox 구동을 위해 Geckodriver를 다운받아 해당 폴더에 둡니다
[https://github.com/mozilla/geckodriver/releases](https://github.com/mozilla/geckodriver/releases)

여기서 `.env`파일을 만들어 줍니다. 여기에는 크롤링에 필요한 정보들을 적습니다

**다음 id,pw는 크롤링하려는 카페에 가입되어있어야 합니다**
```
ID=your_daum_id
PW=your_daum_password
URL=daum_cafe_main_page_url
BOARD=board_name
# BOARD=도촬 시리즈 2
```

마지막으로
```
> python crawl_test.py
```

## License
Free to use. Give a Star on the Repo.

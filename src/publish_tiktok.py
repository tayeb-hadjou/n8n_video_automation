import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


COOKIES_FILE = "./src/tiktok_state.json"
VIDEO_PATH = "./clips/lhumain_epece_a_part/valide/clip_0.mp4"

def run(videoTitle, source, caption, hashtags):
    # ⚙️ Config Chrome avec ton profil existant
    options = Options()
    #ajoter "#" pour chaque hastag
    hashtags = [f"#{tag}" for tag in hashtags]
    caption = f"{caption}{' #' + videoTitle} {' #'+source} {' '.join(hashtags)}"
    #headless
    # options.add_argument("--headless")
    #options.add_argument("--user-data-dir=/home/massi/.config/google-chrome")  # chemin vers ton profil
    #options.add_argument("--profile-directory=Default")  # ou "Profile 1" si tu as plusieurs

    driver = webdriver.Chrome(options=options)
    #headless

    # 1) Aller sur TikTok Upload
    driver.get("https://www.tiktok.com/upload?lang=fr")
    time.sleep(5)

    # 2) Charger cookies si besoin
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        for cookie in cookies["cookies"]:
            # Selenium n’aime pas certains attributs → on nettoie
            cookie.pop("sameSite", None)
            if "expiry" in cookie:
                cookie["expires"] = cookie.pop("expiry")
            try:
                print("🍪 Cookie injecté :", cookie)
                driver.add_cookie(cookie)
            except Exception:
                pass
        driver.refresh()
        print("🍪 Cookies injectés")
        time.sleep(5)
    except Exception:
        print("⚠️ Pas de cookies chargés")

    # 3) Uploader la vidéo
    abs_video_path = os.path.abspath(VIDEO_PATH)
    
    upload_input = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
    )
    upload_input.send_keys(abs_video_path)
    print("🎬 Vidéo envoyée")

    # 📌 Attendre que la zone de texte pour la légende apparaisse
    caption_box = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true']"))
    )
    caption_box.send_keys(CAPTION)
    print("📝 Caption ajoutée")

    #wait 2 min
    time.sleep(120)

    # 📌 Attendre et cliquer sur le bouton publier
    publish_btn = WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-e2e='post_video_button']"))
    )
    publish_btn.click()

    time.sleep(5)

    confirm_btn = WebDriverWait(driver, 60).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class*="TUXButton--primary"]'))
    )
    confirm_btn.click()
    print("🚀 Vidéo publiée !")

    # Attendre 2 minutes avant de fermer (pour laisser TikTok finir le traitement)
    time.sleep(120)
    driver.quit()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Publier une vidéo sur TikTok")
    parser.add_argument("--videoPath", type=str, help="Chemin vers la vidéo")
    parser.add_argument("--videoTitle", type=str, help="Titre de la vidéo")
    parser.add_argument("--source", type=str, help="Source de la vidéo")
    parser.add_argument("--caption", nargs="+", help="Légendes à ajouter à la vidéo")
    parser.add_argument("--hashtag", nargs="+", help="Hashtags à ajouter à la vidéo")
    args = parser.parse_args()

    run(args.videoTitle, args.source, args.caption, args.hashtag)

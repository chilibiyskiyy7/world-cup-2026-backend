import asyncio
import logging
import sqlite3
import aiohttp
import random
import ssl
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, message, WebAppInfo, MenuButtonWebApp, FSInputFile, InputMediaPhoto
from aiohttp import web

BOT_TOKEN = "8799505831:AAFl8g_PHUuDJEvnD2_Z0M5zMEMxZClRTLM"
FOOTBALL_API_URL="https://api.football-data.org/v4/competitions/WC/matches"
API_KEY="95acad5a10ca4075b9603bc0cba4c989"

bot=Bot(token=BOT_TOKEN)
dp=Dispatcher()
logging.basicConfig(level=logging.INFO)
BANNED_USERS=set()

def init_db():
    conn=sqlite3.connect("world_cup_2026.db")
    cursor=conn.cursor()
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS users (
                       user_id INTEGER PRIMARY KEY,
                       username TEXT,
                       points INTEGER DEFAULT 0
                       )
                   """)
    conn.commit()
    conn.close()

async def fetch_football_data(endpoint="matches", params=None):
    url=f"https://api.football-data.org/v4/competitions/WC/{endpoint}"
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; 64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Auth-Token": API_KEY
    }   
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE 
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        try:
            async with session.get(url, headers=headers, params=params,timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Error fetching football data: {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logging.error(f"API Error: {e}")
            return None
        
DEFAULT_LOCAL_PHOTO = "images/default.jpg"
async def safe_send_local_photo(chat_id, photo_path, caption, reply_markup=None, parse_mode="HTML"):
    if os.path.exists(photo_path):
        photo_file = FSInputFile(photo_path)
    else:
        logging.warning(f"File {photo_path} not found! Sending default.")
        photo_file = FSInputFile("images/default.jpg") 
    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo_file,
            caption=caption,
            reply_markup=reply_markup,  
            parse_mode=parse_mode
        )
    except Exception as e:
        logging.error(f"Critical error sending photo: {e}")
        await bot.send_message(
            chat_id=chat_id, 
            text=caption, 
            reply_markup=reply_markup, 
            parse_mode=parse_mode
        )

async def safe_send_local_album(chat_id, photo_paths, caption="", reply_markup=None):
    media = []
    for i, path in enumerate(photo_paths):
        actual_path = path if os.path.exists(path) else "images/default.jpg"
        photo_caption = caption if i == 0 else None
        media.append(
            InputMediaPhoto(
                media=FSInputFile(actual_path),
                caption=photo_caption,
                parse_mode="HTML"
            )
        )
    try:
        await bot.send_media_group(
            chat_id=chat_id, 
            media=media, 
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error sending media group: {e}")
        if caption:
            await bot.send_message(
                chat_id=chat_id, 
                text=caption, 
                reply_markup=reply_markup
            )        

async def safe_send_local_video(chat_id, video_path, caption, reply_markup=None, parse_mode="HTML"):
    if os.path.exists(video_path):
        video_file = FSInputFile(video_path)
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return
        except Exception as e:
            logging.error(f"Critical error sending video {video_path}: {e}")
    logging.warning(f"Fallback triggered for video: {video_path}")
    fallback_photo = "images/default.jpg"
    if os.path.exists(fallback_photo):
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=FSInputFile(fallback_photo),
                caption=caption,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            return
        except Exception as e:
            logging.error(f"Failed to send fallback photo: {e}")
    await bot.send_message(
        chat_id=chat_id,
        text=caption,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )

def get_main_keyboard():
    buttons=[
        [KeyboardButton(text="Latest Matches"), KeyboardButton(text="Today's Matches"), KeyboardButton(text="Random Match")],
        [KeyboardButton(text="Standings"), KeyboardButton(text="Top Scorers")],
        [KeyboardButton(text="Conclusions"), KeyboardButton(text="Other...")]
    ]     
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_infantino_keyboard_1():
        buttons=[
            [KeyboardButton(text="Let's talk about Argentina. There's so much hustle about things that are going with Messi")]
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)        
def get_infantino_keyboard_2():
        buttons=[
            [KeyboardButton(text="What the fuck?")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)            
def get_infantino_keyboard_3():
        buttons=[
            [KeyboardButton(text="Man, fuck you. So it's not Ronaldo's fans delusional. It is truth... wait a minute, what's on that picture behind you?")],
            [KeyboardButton(text="Hmmm. Okayy. Let's change the subject. What the fuck was that ballogan move.")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)           
def get_infantino_keyboard_4():
        buttons=[
            [KeyboardButton(text="Man fuck you. I got to look.")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_5():
        buttons=[
            [KeyboardButton(text="What the fuck is this shit? man you're serious?")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_6():
        buttons=[
            [KeyboardButton(text="Who are you calling? I'll be quiet just let me go.")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_7():
        buttons=[
            [KeyboardButton(text="JUST LET ME GO I WON'T TELL IT")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_8():
        buttons=[
            [KeyboardButton(text="Whose order? Don't it from the man, who even don't know what is red card? Or from the one who stole Madueke's medals? wait a minute, what's on that picture behind you?")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_9():
        buttons=[
            [KeyboardButton(text="Fuck. Man I'd better never seen that shit, it is gross.")]  
            ]
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True) 
def get_infantino_keyboard_10():
        buttons=[
            [KeyboardButton(text="I knew you are fuckin' humanoid.")]  
            ]
def get_infantino_keyboard_11():
        buttons=[
            [KeyboardButton(text="No bro I got to look")]  
            ]        
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_conc_keyboard_0():
        buttons=[
            [KeyboardButton(text="Messi")]  
            ] 
def get_conc_keyboard_1():
        buttons=[
            [KeyboardButton(text="Saka")]  
            ]        
def get_conc_keyboard_2():
        buttons=[
            [KeyboardButton(text="Ronaldo")]  
            ]
def get_conc_keyboard_3():
        buttons=[
            [KeyboardButton(text="Mbappe")]  
            ]
def get_conc_keyboard_4():
        buttons=[
            [KeyboardButton(text="Olise")]  
            ]
def get_conc_keyboard_5():
        buttons=[
            [KeyboardButton(text="Heroes")]  
            ]
def get_conc_keyboard_6():
        buttons=[
            [KeyboardButton(text="Losers")]  
            ]
def get_conc_keyboard_7():
        buttons=[
            [KeyboardButton(text="Top Scorers")]  
            ]
def get_conc_keyboard_8():
        buttons=[
            [KeyboardButton(text="Final")]  
            ]                                        
def get_optional_keyboard(menu_type="matches"):
    builder = InlineKeyboardBuilder() 
    if menu_type == "random_match":
        builder.row(
            InlineKeyboardButton(text="Refresh", callback_data="refresh:random"), 
            InlineKeyboardButton(text="Back", callback_data="back:random")
        ) 
        builder.row(
            InlineKeyboardButton(text="Bot's Prediction", callback_data="bot_prediction"), 
            InlineKeyboardButton(text="Make prediction", callback_data="make_prediction")
        )
        
    elif menu_type == "standings":    
        builder.row(
            InlineKeyboardButton(text="Group Stage", callback_data="show_groupstage"),
            InlineKeyboardButton(text="Playoffs", callback_data="show_playoffs")
        )
        
    elif menu_type == "show_groupstage":    
        letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
        for letter in letters:
            builder.add(InlineKeyboardButton(text=f"Group {letter}", callback_data=f"view_group:{letter}"))
        builder.adjust(3)
        builder.row(InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back:standings"))
    elif menu_type == "show_playoffs":
        stage = [
            ("Round of 32", "LAST_32"),        
            ("Round of 16", "LAST_16"),        
            ("Quarter-finals", "QUARTER_FINALS"),
            ("Semi-finals", "SEMI_FINALS"),
            ("Final", "FINAL")
        ]
        for text, code in stage:
            builder.add(InlineKeyboardButton(text=text, callback_data=f"view_playoffs:{code}"))
        builder.adjust(3)    
        builder.row(InlineKeyboardButton(text="⬅️ Back to Menu", callback_data="back:standings"))
    elif menu_type == "other":
        builder.row(InlineKeyboardButton(text="Kylian Mbappe", callback_data="mbappe"))
        builder.row(InlineKeyboardButton(text="Infantino", callback_data="infantino_start"))
    elif menu_type == "mbappe":
        builder.row(InlineKeyboardButton(text="Yeah", callback_data="mbappe_yes"), InlineKeyboardButton(text="Nope", callback_data="mbappe_no"))
    elif menu_type=="mbappe_no":
        builder.row(InlineKeyboardButton(text="Back to Menu", callback_data="back:other"))                 
    return builder.as_markup()
       

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id=message.from_user.id
    username=message.from_user.username or "Anonymous"
    conn=sqlite3.connect("world_cup_2026.db")
    cursor=conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?) ", (user_id, username))
    conn.commit()
    conn.close()
    await message.answer(f"Hello, {username}! Welcome to the World Cup 2026 Bot. \nChoose an option from the menu below:", reply_markup=get_main_keyboard())


@dp.message(F.text =="Random Match")
async def handle_random_match(message:Message):
    try:
        data=await fetch_football_data()
        if data and "matches" in data:
            matches=data["matches"]
            random_match=random.choice(matches)
            home_team=random_match["homeTeam"].get("name") or "TBD"
            away_team=random_match["awayTeam"].get("name") or "TBD"
            raw_date=random_match.get("utcDate")
            if raw_date:
                dt=datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
                match_date=dt.strftime("%d.%m.%Y at %H:%M")
            else:
                match_date="Unknown Date"
            match_id = random_match.get("id", f"{home_team}_vs_{away_team}".replace(" ", "_"))
            response_text=(f"Random Match World Cup 2026! \nDate: {match_date} \nHome Team: {home_team} VS {away_team} :Away Team")
            await message.answer(response_text, reply_markup=get_optional_keyboard("random_match"))
        else:
            await message.answer("Sorry, couldn't fetch match data at the moment. Try again later.")    
    except Exception as e:
        logging.error(f"Error processing football data: {e}")
        await message.answer("Sorry, an error occured. Try again later.")

async def random_match_handler(request):
    data=await fetch_football_data()
    headers = {"Access-Control-Allow-Origin": "*"}
    if data and "matches" in data and len(data["matches"])>0:
        matches=data["matches"]
        random_match=random.choice(matches)
        formatted_match={
                    "match_id": random_match.get("id"),
                    "utcDate": random_match.get("utcDate"),
                    "home_team": random_match.get("homeTeam", {}).get("name") or "TBD",
                    "away_team": random_match.get("awayTeam", {}).get("name") or "TBD",
                    "home_score": random_match.get("score", {}).get("fullTime", {}).get("home", "?"),
                    "away_score": random_match.get("score", {}).get("fullTime", {}).get("away", "?")
                }   
        if formatted_match["home_score"] is None:
            formatted_match["home_score"] = "?"
        if formatted_match["away_score"] is None:
            formatted_match["away_score"] = "?"
        return web.json_response({"matches":[formatted_match]}, headers=headers)
    return web.json_response({"matches": []}, headers=headers)
            

@dp.message(F.text =="Today's Matches")
async def handle_todays_matches(message:Message):
    try:
        data=await fetch_football_data()
        if data and "matches" in data:
            matches=data["matches"]
            now=datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            todays_matches = [match for match in matches if match.get("utcDate", "").startswith(today_str)]
            response_text=f"**Today's Matches World Cup 2026:**\n\n"
            match_count=0
            if todays_matches:
                for match in todays_matches:
                    if match["utcDate"].startswith(today_str):
                       match_count += 1
                    home_team=match["homeTeam"].get("name") or "TBD"
                    away_team=match["awayTeam"].get("name") or "TBD"
                    raw_date=match.get("utcDate")
                    if raw_date:
                        dt=datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
                        match_date=dt.strftime("%d.%m.%Y at %H:%M")
                    else:
                       match_date="Unknown Date"
                    match_id=match.get("id", f"{home_team} VS {away_team}".replace(" ", "_"))
                    response_text+=(f"{match_date} \n**{home_team}** VS **{away_team}**\n\n")
            if match_count>0:
                await message.answer(response_text, parse_mode="Markdown")
            else:
                await message.answer("No matches scheduled for today.")
        else:
            await message.answer("Sorry, couldn't fetch match data at the moment.")
    except Exception as e:
        logging.error(f"Error in todays matches: {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

async def today_matches_handler(request):
    data= await fetch_football_data()
    headers = {"Access-Control-Allow-Origin": "*"}
    if data and "matches" in data:
        matches=data["matches"]
        now=datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        todays_matches = []
        for match in matches: 
            if match.get("utcDate", "").startswith(today_str):
                todays_matches.append({"utcDate":match.get("utcDate"), "home": match.get("homeTeam", {}).get("name") or "TBD",
                    "away": match.get("awayTeam", {}).get("name") or "TBD"})
        return web.json_response({"matches":todays_matches}, headers=headers)
    return web.json_response({"matches": []}, headers=headers)







@dp.message(F.text =="Latest Matches")
async def handle_latest_matches(message:Message):
    try:
        match_params={"status":"FINISHED", "limit":5}
        data=await fetch_football_data(params=match_params)
        if data and "matches" in data:
            matches=data["matches"]
            if matches:
                played_matches = [
                    m for m in matches 
                    if m.get("status") == "FINISHED" or m.get("score", {}).get("fullTime", {}).get("home") is not None
                ]
                if played_matches:
                    latest_matches=played_matches[-5:][::-1]
                    response_text="**Latest Matches World Cup 2026:**\n\n"
                    for match in latest_matches:
                        home_team=match["homeTeam"].get("name") or "TBD"
                        away_team=match["awayTeam"].get("name") or "TBD"
                        home_score=match.get("score", {}).get("fullTime", {}).get("home", "?")
                        away_score=match.get("score", {}).get("fullTime", {}).get("away", "?")
                        raw_date=match.get("utcDate")
                        if raw_date:
                            dt=datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
                            match_date=dt.strftime("%d.%m.%Y at %H:%M")
                        else:
                            match_date="Unknown Date"
                        match_id=match.get("id", f"{home_team} VS {away_team}".replace(" ", "_"))
                        response_text+=f"{match_date} \n **{home_team}** `{home_score}` VS `{away_score}` **{away_team}**\n\n"
                    await message.answer(response_text, parse_mode="Markdown")
                else:
                    await message.answer("No finished matches yet.")
        else:
            await message.answer("Sorry, couldn't fetch latest matches data at the moment.")
    except Exception as e:
        logging.error(f"Error in latest matches: {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

async def latest_matches_handler(request):
    match_params = {"status": "FINISHED", "limit": 5}
    data = await fetch_football_data(params=match_params)
    headers = {"Access-Control-Allow-Origin": "*"}
    if data and "matches" in data:
        matches=data["matches"]
        if matches:
                played_matches = [
                    m for m in matches 
                    if m.get("status") == "FINISHED" or m.get("score", {}).get("fullTime", {}).get("home") is not None
                ]
                if played_matches:
                    latest_matches=played_matches[-5:][::-1]
                    result=[]
                    for match in latest_matches:
                        result.append({
                            "utcDate": match.get("utcDate"),
                            "home_team": match.get("homeTeam", {}).get("name") or "TBD",
                            "away_team": match.get("awayTeam", {}).get("name") or "TBD",
                            "home_score": match.get("score", {}).get("fullTime", {}).get("home", "?"),
                            "away_score": match.get("score", {}).get("fullTime", {}).get("away", "?")
                        })
                    return web.json_response({"matches":result}, headers=headers)
    return web.json_response({"matches": []}, headers=headers)
         
                        



@dp.message(F.text=="Top Scorers")
async def handle_top_scorers(message:Message):
    try:
        data=await fetch_football_data(endpoint="scorers")
        if data and "scorers" in data:
            scorers=data["scorers"][:10]
            if scorers:
                top_10_scorers=scorers[:10]
                response_text="**Top Scorers World Cup 2026:**\n\n"
                for i, scorer in enumerate(top_10_scorers, 1):
                    player_name=scorer.get("player", {}).get("name") or "Unknown Player"
                    team_name=scorer.get("team", {}).get("name") or "Unknown Team"
                    goals=scorer.get("goals", 0)
                    response_text+=f"{i}.**{player_name}** ({team_name}) - {goals} goals!\n\n"
                await message.answer(response_text, parse_mode="Markdown")
            else:
                await message.answer("No top scorers' data yet.")
        else:
            await message.answer("Sorry, couldn't fetch top scorers' data at the moment.")
    except Exception as e:
        logging.error(f"Error in 'Top Scorers': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

async def top_scorers_handler(request):
    data=await fetch_football_data(endpoint="scorers")
    headers = {"Access-Control-Allow-Origin": "*"}
    if data and "scorers" in data:
        scorers=data["scorers"][:10]   
        result=[]
        for scorer in scorers:
            player = scorer.get("player", {})
            team = scorer.get("team", {})
            result.append({
                    "player_id":player.get("id"),
                    "player_name": player.get("name") or "Unknown Player",
                    "team_name": team.get("name") or "Unknown Team",
                    "goals": scorer.get("goals", 0),
                    "assists": scorer.get("assists", 0),
                    "played_matches": scorer.get("playedMatches", 0),
                    "penalties": scorer.get("penalties", 0)

            })    
        return web.json_response({"scorers":result}, headers=headers)
    return web.json_response({"scorers": []}, headers=headers)


@dp.message(F.text=="Standings")
async def handle_standings(message:Message):
    try:
        response_text="Choose an option below!"
        await message.answer(response_text, reply_markup=get_optional_keyboard("standings"), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in 'Standings': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.message(F.text=="Conclusions")
async def handle_conclusions(message:Message):
    try:
        response_text="Spain - World Cup 2026 Champions! (and Tramp too) \n\nRodri - owner of WC 2026 Ballon D'or! \n\nCubarsi - best young player of WC 2026! \n\nUnai Simon - owner of WC 2026 Golden Glove! \n\n🐐Ferran Torres🐐 - MVP of the final!"
        photos=["images/champions_wc2026.jpg", "images/rodri.jpg", "images/cubarsi.jpg", "images/simon.jpg", "images/ferran.jpg"]
        await safe_send_local_album(
            chat_id=message.chat.id,
            photo_paths=photos,
            caption=response_text,
            reply_markup=get_conc_keyboard_0() 
        )
    except Exception as e:
        logging.error(f"Error in 'Conclusions': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.message(F.text=="Messi")
async def handle_conclusions(message:Message):
    try:
        response_text="Messi did it to the final again! 3rd time. He really did it to the final in 50%% of World Cups he was in. I think we should pay respect to Infantino. \n\nOn this WC, while being an 39 years old, he did one of the greatest individual perfomances. 8+4 in World Cup in that age is incredable."
        photos=["images/messi1.jpg", "images/messi2.jpg", "images/messi3.png", "images/messi4.jpg", "images/messi5.jpg"]
        await safe_send_local_album(
            chat_id=message.chat.id,
            photo_paths=photos,
            caption=response_text,
            reply_markup=get_conc_keyboard_1() 
        )
    except Exception as e:
        logging.error(f"Error in 'Conclusions': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.message(F.text=="Saka")
async def handle_conclusions(message:Message):
    try:
        response_text="Messi's perfomance is nothing compared to this monster perfomance. \n\nDid Messi score hat-trick vs France? \n\nDid Messi score hat-trick in knockouts? \n\nDid ever Messi win EPL? \n\n\n\nBut this monster did."
        video_path="saka.mp4"
        await safe_send_local_video(
            chat_id=message.chat.id,
            video_path=video_path,
            caption=response_text,
            reply_markup=get_conc_keyboard_2() 
        )
    except Exception as e:
        logging.error(f"Error in 'Conclusions': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.message(F.text=="Ronaldo")
async def handle_conclusions(message:Message):
    try:
        response_text="He's back! Or not? \n\n2 goals against Uzbekistan and 1 penalty vs Croatia while Messi did 8+4. Fate is not on Ronaldo's side again. \n\n\nIt great that at least Messi didn't win, he would go crazy."
        photos=["images/ronaldo1.jpg", "images/ronaldo2.jpg", "images/ronaldo3.jpg", "images/ronaldo4.jpg", "images/ronaldo5.jpg", "images/ronaldo6.jpg", "images/ronaldo7.jpg",]
        await safe_send_local_album(
            chat_id=message.chat.id,
            photo_paths=photos,
            caption=response_text,
            reply_markup=get_conc_keyboard_3() 
        )
    except Exception as e:
        logging.error(f"Error in 'Conclusions': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.message(F.text=="Other...")
async def handle_other(message: Message):
    try:
        response_text="Other options:"
        await message.answer(response_text, reply_markup=get_optional_keyboard("other"), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in 'Other': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")

@dp.callback_query()
async def handle_all_callbacks(callback_query: CallbackQuery):
    await callback_query.answer()  # Сразу гасим часики на кнопке
    data = callback_query.data
    
    if data == "mbappe":
        await handle_mbappe(callback_query)
    elif data == "mbappe_yes":
        await handle_mbappe_yes(callback_query)
    elif data == "mbappe_no":
        await handle_mbappe_no(callback_query)
    elif data == "infantino_start":  
        await process_infantino_inline(callback_query)    
    elif data.startswith("show_groupstage"):
        await show_groupstage(callback_query)
    elif data.startswith("view_group:"):
        await view_universal_group(callback_query)
    elif data.startswith("show_playoffs"):
        await show_playoffs(callback_query)
    elif data.startswith("view_playoffs:"):
        await view_universal_playoffs(callback_query)
    elif data.startswith("back:"):
        await universal_back_handler(callback_query)
    elif data.startswith("refresh:"):
        await refresh_universal_refresh(callback_query)

async def handle_mbappe(callback_query: CallbackQuery):
    try:
        response_text="Hi. You might know me. I'n Vini JR, and I'm about to say something.There is a rumors that Kylian Mbappe could be a reason France might not win the World Cup 2026. Someone even call him 'dictator' by joke. People in Real Madrid FC, including me, is frustraited with his behavior. Remember that 'suddenly-went-to-Italy' accident? But I'm not gonna stop with hollow words only. I got the bunch of mediafiles that proofs evilness of this fuckin vicious turtle. Wanna see it?" 
        photo_path="images/vini_crying.jpg"
        await safe_send_local_photo(
            chat_id=callback_query.message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_optional_keyboard("mbappe")
        )
    except Exception as e:
        logging.error(f"Error in 'Other': {e}", exc_info=True)
        await callback_query.message.answer("Sorry, an error occurred. Try again later.")


async def handle_mbappe_yes(callback_query: CallbackQuery):
    try:
        user_id = callback_query.from_user.id
        response_text="You're an asshole. Now GET OUT OF MY EYES YOU FUCKIN IDIOT!!!"
        photo_path="images/dictator1.png"
        await safe_send_local_photo(
            chat_id=callback_query.message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            )
    except Exception as e:
        logging.error(f"Error in 'Other': {e}", exc_info=True)
        await callback_query.message.answer("Sorry, an error occurred. Try again later.")


async def handle_mbappe_no(callback_query: CallbackQuery):
    try:
        response_text="You're a good kid. You were right for not listening to this brasilian drama queen."
        photo_path="images/dictator2_happy.png"
        await safe_send_local_photo(
            chat_id=callback_query.message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_optional_keyboard("mbappe_no")
            )
    except Exception as e:
        logging.error(f"Error in 'Other': {e}", exc_info=True)
        await callback_query.message.answer("Sorry, an error occurred. Try again later.")
        

async def process_infantino_inline(callback: CallbackQuery):
    response_text="Hi! You're a lucky kid! Today, on 14th of July, you'll have an opportunity to ask me some questions. Go on!"
    photo_path="images/infantino_default.png"
    await safe_send_local_photo(
            chat_id=callback.message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_1()
            )    
        
@dp.message(F.text=="Let's talk about Argentina. There's so much hustle about things that are going with Messi")
async def infantino_argentina(message:Message):
    response_text="Oh... Argentina... My heart belongs to argentina. I almost became Christian Eriksen when my darling played against Cabo Verde. But I'm glad I call referee in time. I told 'em that Messi must win World Cup."
    photo_path="images/infantino_argentina.png"        
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_2()
            )

@dp.message(F.text=="What the fuck?")
async def infantino_neutral(message:Message):
    response_text="Oh. Um... I mean.. I mean I'n neutral."
    photo_path="images/infantino_scared.png"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_3()
            )
    
@dp.message(F.text=="Man, fuck you. So it's not Ronaldo's fans delusional. It is truth... wait a minute, what's on that picture behind you?")
async def infantino_scared(message:Message):
    response_text="It's nothing. Nothing special, nothing interest. Just keep out of that thing. O-okay?"
    photo_path="images/infantino_stress.png"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_4()
            )
    
@dp.message(F.text=="Man fuck you. I got to look.")
async def infantino_family(message:Message):
    response_text="..."
    photo_path="images/infantino_family.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_5()
            )
    
@dp.message(F.text=="What the fuck is this shit? man you're serious?")
async def infantino_angry(message:Message):
    response_text="You know too much. Now I'll get the permission of killin' you. \n\n*Phone's ringing*"
    photo_path="images/infantino_calling.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_6()
            )

@dp.message(F.text=="Who are you calling? I'll be quiet just let me go.")
async def infantino_call(message:Message):
    response_text="Infantino: Hi, daddy. S-sorry for disturbing you. But here one asshole found out about status of our private relationship. \n\n Messi: Camera vovo. Camera vovo. Odna bolshaya vovo. kill him. and go hom make mi fut massage."
    photo_path="images/infantino_messi.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_7()
            )

@dp.message(F.text=="JUST LET ME GO I WON'T TELL IT")
async def infantino_mad(message:Message):
    response_text="And that's your last words? Boring \n\n*Infantino shot you*"
    photo_path="images/infantino_mad.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_main_keyboard()
            )

@dp.message(F.text=="Hmmm. Okayy. Let's change the subject. What the fuck was that ballogan move.")
async def infantino_ballogan(message:Message):
    response_text="Honestly, that was not my decision. That was an order."
    photo_path="images/infantino_order.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_8()
            )

@dp.message(F.text=="Whose order? Don't it from the man, who even don't know what is red card? Or from the one who stole Madueke's medals? wait a minute, what's on that picture behind you?")
async def infantino_stress(message:Message):
    response_text="Oh. Um... I mean.. I mean.. I mean that was absolutely my decision. And I don't understand what are you talking about. And keep out of that picture. And forget about what I was saying. Deal?"
    photo_path="images/infantino_stress.png"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_11()
            )
    
    
@dp.message(F.text=="No bro I got to look")
async def infantino_tramp(message:Message):
    response_text="..."
    photo_path="images/infantino_tramp.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_9()
            )
    
@dp.message(F.text=="Fuck. Man I'd better never seen that shit, it is gross.")
async def infantino_humanoid(message:Message):
    response_text="We are dissapointed with your behavior. Now we have to kill you."
    photo_path="images/infantino_humanoid.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_infantino_keyboard_10()
            )  

@dp.message(F.text=="I knew you are fuckin' humanoid.")
async def infantino_humanoid_mad(message:Message):
    response_text="Of course I am! How then I was on every world cup game? That was my clones. Bye! \n\n*Allien-Infantino shot you."
    photo_path="images/infantino_humanoid_mad.jpg"
    await safe_send_local_photo(
            chat_id=message.chat.id,
            photo_path=photo_path,
            caption=response_text,
            reply_markup=get_main_keyboard()
            )      

async def show_groupstage(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        response_text="Choose a group to look below."
        await callback_query.message.edit_text(response_text, reply_markup=get_optional_keyboard("show_groupstage"), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")

                                 

async def view_universal_group(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        group_letter = callback_query.data.split(":")[1]
        data= await fetch_football_data(endpoint="standings")
        response_text=f"*Group {group_letter}:*\n\n"
        group_table=None
        if data and "standings" in data:
            for group in data["standings"]:
                if group_letter in group["group"].upper():
                    group_table=group["table"]
                    break
            if group_table:
                response_text += "```text\n"
                response_text += "Team         | G | Pts\n"
                response_text += "-----------------------\n"    
                for team in group_table:
                   name=team["team"]["name"]
                   short_name=name[:12]
                   games=team["playedGames"]
                   points=team["points"]
                   response_text+=f"{short_name.ljust(12)} | {games} | {points}\n"
                response_text += "```"
                await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard("show_groupstage"), parse_mode="Markdown")
            else:
                await callback_query.message.edit_text(f"Group {group_letter} not found.")
        else:
            await callback_query.message.edit_text("Sorry, couldn't fetch data at the moment. Try again later.")    
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")

                

async def show_playoffs(callback_query:CallbackQuery):
    try:
        await callback_query.answer()
        response_text="Choose a stage below."
        await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard("show_playoffs"))
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")


async def view_universal_playoffs(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        stage_code = callback_query.data.split(":")[1]
        
        # Шаг 1: Запрашиваем "matches", а не пустой эндпоинт!
        data = await fetch_football_data(endpoint="matches") 
        
        playoff_matches = []
        if data and "matches" in data:
            for match in data["matches"]:
                # Шаг 2: Сравниваем стадию с тем, что прислал API
                if match.get("stage") == stage_code:
                    playoff_matches.append(match)
        
        if playoff_matches:
            stage_title = stage_code.replace("_", " ").title()
            response_text = f"🏆 *World Cup 2026 — {stage_title}*\n\n"
            
            for match in playoff_matches:
                home_team = match.get("homeTeam", {}).get("name") or "TBD"
                away_team = match.get("awayTeam", {}).get("name") or "TBD"
                home_score = match.get("score", {}).get("fullTime", {}).get("home")
                away_score = match.get("score", {}).get("fullTime", {}).get("away")
                
                if home_score is not None and away_score is not None:
                    score_str = f"*{home_score} : {away_score}*"
                else:
                    score_str = "vs"
                response_text += f"⚽ {home_team} {score_str} {away_team}\n"
            
            await callback_query.message.edit_text(
                text=response_text, 
                reply_markup=get_optional_keyboard("show_playoffs"), 
                parse_mode="Markdown"
            )
        else:
            await callback_query.message.edit_text(
                text=f"Matches for stage {stage_code} not found or not scheduled yet.",
                reply_markup=get_optional_keyboard("show_playoffs")
            )
            
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")


async def universal_back_handler(callback_query: CallbackQuery):
    try:
        back_target = callback_query.data.split(":")[1] 
        if back_target == "random":
            await callback_query.answer(text="Returned to main menu:", reply_markup=get_main_keyboard())
            await callback_query.message.delete()
        elif back_target == "standings":
            response_text = "Choose a stage below:"
            await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard(menu_type="standings"),parse_mode="Markdown")
        elif back_target == "other":
            response_text = "Other options:"
            await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard(menu_type="other"),parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in universal back handler: {e}", exc_info=True)
        await callback_query.message.answer("Error going back.")


    


async def refresh_universal_refresh(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
        parts = callback_query.data.split(":")
        refresh_type = parts[1] if len(parts) > 1 else ""
        if refresh_type=="random":
            data=await fetch_football_data()
            if data and "matches" in data and data["matches"]:
                matches=data["matches"]
                random_match=random.choice(matches)
                home_team=random_match["homeTeam"].get("name") or "TBD"
                away_team=random_match["awayTeam"].get("name") or "TBD"
                raw_date=random_match.get("utcDate")
                if raw_date:
                    dt=datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ")
                    match_date=dt.strftime("%d.%m.%Y at %H:%M")
                else:
                    match_date="Unknown Date"    
                match_id = random_match.get("id", f"{home_team}_vs_{away_team}".replace(" ", "_"))
                response_text=(f"Random Match World Cup 2026! \nDate: {match_date} \nHome Team: {home_team} VS {away_team} :Away Team")
                await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard("random_match"))
            else:
                await callback_query.message.edit_text("Sorry, couldn't fetch match data at the moment. Try again later.")    
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")
               


async def main():
    init_db()
    print("Bot is running... Press Cntl+C to stop.")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Open App",
            web_app=WebAppInfo(url="https://chilibiyskiyy7.github.io/world-cup-2026-app/")
        )
    )
    app=web.Application()
    app.router.add_get("/api/matches/today", today_matches_handler)
    app.router.add_get("/api/latest/matches", latest_matches_handler)
    app.router.add_get("/api/top/scorers", top_scorers_handler)
    app.router.add_get("/api/random/match", random_match_handler)
    runner=web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8085))  
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())            


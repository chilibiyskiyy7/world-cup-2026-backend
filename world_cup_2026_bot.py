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
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, message, WebAppInfo, MenuButtonWebApp, FSInputFile
from aiogram import Bot 
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN", "8665805981:AAHd8Tm2PuMueSlFswAiRseOBDFcoBTIaWQ")
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


def get_main_keyboard():
    buttons=[
        [KeyboardButton(text="Latest Matches"), KeyboardButton(text="Today's Matches"), KeyboardButton(text="Random Match")],
        [KeyboardButton(text="Standings"), KeyboardButton(text="Top Scorers")],
        [KeyboardButton(text="Other...")]
    ]     
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
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
        stage=[
            ("Round of 32", "ROUND_OF_32"), 
            ("Round of 16", "ROUND_OF_16"),
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
    elif menu_type == "mbappe":
        builder.row(InlineKeyboardButton(text="Yeah", callback_data="mbappe_yes"), InlineKeyboardButton(text="Nope", callback_data="mbappe_no"))
    elif menu_type=="mbappe_no":
        builder.row(InlineKeyboardButton(text="Back to Menu", callback_data="back:other"))             
    return builder.as_markup()

@dp.message(lambda msg: msg.from_user.id in BANNED_USERS)
async def check_ban_status(message: Message):
    if message.from_user.id in BANNED_USERS:
        if message.text and message.text.strip().lower() == "kylian mbappe is not dictator 67":
            BANNED_USERS.remove(message.from_user.id)
            await message.answer("Mbappe forgave you. You are unbanned now.", reply_markup=get_main_keyboard())
            return
        await message.answer("I banned you. If you want to be unbanned, send the correct password, asshole.\n\nMbappe")
        return

@dp.callback_query()
async def check_callback_ban(callback_query: CallbackQuery):
    if callback_query.from_user.id in BANNED_USERS:
        await callback_query.answer("You are BANNED! Type password in chat.", show_alert=True)
        return
        
    data = callback_query.data
    if data == "mbappe":
        await handle_mbappe(callback_query)
    elif data == "mbappe_yes":
        await handle_mbappe_yes(callback_query)
    elif data == "mbappe_no":
        await handle_mbappe_no(callback_query)
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

@dp.message(F.text=="Other...")
async def handle_other(message: Message):
    try:
        response_text="Other options:"
        await message.answer(response_text, reply_markup=get_optional_keyboard("other"), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in 'Other': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")


async def handle_mbappe(callback_query: CallbackQuery):
    try:
        await callback_query.answer()
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
        await callback_query.answer()
        user_id = callback_query.from_user.id
        BANNED_USERS.add(user_id)
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
        await callback_query.answer()
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
        data = await fetch_football_data(endpoint="")
        
        playoff_matches = []
        if data and "matches" in data:
            # ЦИКЛ №1: ТОЛЬКО собираем матчи нужной стадии, ничего больше!
            for match in data["matches"]:
                if match.get("stage") == stage_code:
                    playoff_matches.append(match)
        
        # ОТСТУП УМЕНЬШИЛСЯ: Мы вышли из цикла! 
        # Теперь один раз обрабатываем собранный список:
        if playoff_matches:
            stage_title = stage_code.replace("_", " ").title()
            response_text = f"🏆 *World Cup 2026 — {stage_title}*\n\n"
            
            # ЦИКЛ №2: Красиво оформляем собранные матчи в текст
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
            
            # Один-единственный раз редактируем сообщение
            await callback_query.message.edit_text(
                text=response_text, 
                reply_markup=get_optional_keyboard("show_playoffs"), 
                parse_mode="Markdown"
            )
        else:
            # Если после окончания цикла список остался пустым
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


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
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, message, WebAppInfo, MenuButtonWebApp
from aiogram import Bot 
from aiohttp import web

BOT_TOKEN="8799505831:AAFTzkdhGHkL5-yFI3jUHJJMAUVKA4Uz_Ss"
FOOTBALL_API_URL="https://api.football-data.org/v4/competitions/WC/matches"
API_KEY="95acad5a10ca4075b9603bc0cba4c989"

bot=Bot(token=BOT_TOKEN)
dp=Dispatcher()
logging.basicConfig(level=logging.INFO)

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
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Error fetching football data: {response.status} for {endpoint}")
                    return None
        except Exception as e:
            logging.error(f"API Error: {e}")
            return None

def get_main_keyboard():
    buttons=[
        [KeyboardButton(text="Latest Matches"), KeyboardButton(text="Today's Matches"), KeyboardButton(text="Random Match")],
        [KeyboardButton(text="Standings"), KeyboardButton(text="Top Scorers"), KeyboardButton(text="My Predictions")],
        [KeyboardButton(text="Bot's Predictions"), KeyboardButton(text="My Points")]
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
        todays_matches = [match for match in matches if match.get("utcDate", "").startswith(today_str)]
        return web.json_response({"matches":todays_matches}, headers=headers)
    return web.json_response({"matches": []}, headers=headers)
app=web.Application()
app.router.add_get("/api/matches/today", today_matches_handler)





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
    


@dp.message(F.text=="Standings")
async def handle_standings(message:Message):
    try:
        response_text="Choose an option below!"
        await message.answer(response_text, reply_markup=get_optional_keyboard("standings"), parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in 'Standings': {e}", exc_info=True)
        await message.answer("Sorry, an error occurred. Try again later.")


@dp.callback_query(F.data.startswith("show_groupstage"))
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

                                 
@dp.callback_query(F.data.startswith("view_group:"))
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

                
@dp.callback_query(F.data.startswith("show_playoffs"))
async def show_playoffs(callback_query=CallbackQuery):
    try:
        await callback_query.answer()
        response_text="Noy available yet. Come back on 8th July of 2026!"
        await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard("standings"))
    except Exception as e:
        logging.error(f"Error processing football data: {e}", exc_info=True)
        try:
            await callback_query.message.edit_text("Sorry, an error occured. Try again later.")
        except Exception:
            await callback_query.message.answer("Error. Try again later.")

@dp.callback_query(F.data.startswith("back:"))
async def universal_back_handler(callback_query: CallbackQuery):
    try:
        back_target = callback_query.data.split(":")[1] 
        if back_target == "random":
            await callback_query.answer(text="Returned to main menu:", reply_markup=get_main_keyboard())
            await callback_query.message.delete()
        elif back_target == "standings":
            response_text = "Choose a stage below:"
            await callback_query.message.edit_text(text=response_text, reply_markup=get_optional_keyboard(menu_type="standings"),parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Error in universal back handler: {e}", exc_info=True)
        await callback_query.message.answer("Error going back.")


    

@dp.callback_query(F.data.startswith("refresh:"))
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
    runner=web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))  
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())            


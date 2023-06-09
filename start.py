from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import *
from models import *
import json
from flask import jsonify

@app.route("/")
def hello():
    return render_template("/index.html")

@app.route("/gmlist")
def gm_list():
    users = db.session.execute(db.select(Players).filter_by(title="GM").order_by(Players.name)).scalars()
    json_data = []
    for user in users:
        user_data = [user.__repr__()]
        json_data.append(user_data)

    return json_data

@app.route("/draw%")
def draw():
    draw = Game.query.filter_by(result="1/2-1/2").count()
    total_games = Game.query.count()
    return str(draw * 100 / total_games)

@app.route("/white/win%")
def white_win():
    win = Game.query.filter_by(result="1-0").count()
    total_games = Game.query.count()
    return str(win * 100 / total_games)

@app.route("/users/create", methods=["GET", "POST"])
def user_create():
    if request.method == "POST":
        user = Players(
            name=request.form["name"],
            player_elo=request.form["player_elo"],
            last_active_date=request.form["date"],
            last_active_time=request.form["time"]
        )
        db.session.add(user)
        db.session.commit()
        return str(user)

    return render_template("index.html", utc_dt = "User Created!")

@app.route("/user/win/white", methods=["POST"])
def findWinPost():
    if request.method == "POST":
        name = request.form["name"]
        win_percentage = db.session.query(
        Game.white_player_name,
        Players.last_active_date,
        Players.player_elo,
        db.func.count(Game.white_player_name == name).label('total_games'),
        db.func.sum(db.case(((Game.white_player_name == name) & (Game.result == '1-0'), 1), else_=0)).label('total_wins'),
        db.func.sum(db.case(((Game.white_player_name == name) & (Game.result == '0-1'), 1), else_=0)).label('total_losses'),
        db.func.sum(db.case(((Game.white_player_name == name) & (Game.result == '1/2-1/2'), 1), else_=0)).label('total_draws')
    ).join(
        Players, Game.white_player_name == Players.name
    ).filter(
        Game.white_player_name == name
    ).group_by(
        Game.white_player_name
    ).first()
        win_percentage = {
        'total_games': win_percentage.total_games,
        'total_wins': win_percentage.total_wins,
        'total_losses': win_percentage.total_losses,
        'total_draws': win_percentage.total_draws,
        'last_active_time': win_percentage.last_active_date,
        'player_elo': win_percentage.player_elo,
        'win_percentage': (win_percentage.total_wins / win_percentage.total_games) * 100 if win_percentage.total_games > 0 else None
    }
        return win_percentage


@app.route("/user/win/white/<string:name>")
def findWin(name):
    win_percentage = db.session.query(
        Game.white_player_name,
        Players.last_active_date,
        Players.player_elo,
        db.func.count(Game.white_player_name==name).label('total_games'),
        db.func.sum(db.case(((Game.white_player_name==name) & (Game.result == '1-0'), 1), else_=0)).label('total_wins'),
        db.func.sum(db.case(((Game.white_player_name==name) & (Game.result == '0-1'), 1), else_=0)).label('total_losses'),
        db.func.sum(db.case(((Game.white_player_name==name) & (Game.result == '1/2-1/2'), 1), else_=0)).label('total_draws')
    ).join(
        Players, Game.white_player_name == Players.name
    ).filter(
        Game.white_player_name == name
    ).group_by(
        Game.white_player_name
    ).first()

    win_percentage = {
    'total_games': win_percentage.total_games,
    'total_wins': win_percentage.total_wins,
    'total_losses': win_percentage.total_losses,
    'total_draws': win_percentage.total_draws,
    'last_active_time': win_percentage.last_active_date,
    'player_elo': win_percentage.player_elo,
    'win_percentage': (win_percentage.total_wins / win_percentage.total_games) * 100 if win_percentage.total_games > 0 else None
    }

    return win_percentage

@app.route("/getNumChecks", methods = ["POST"])
def checkCount():
    opening_start=request.form["opening"],
    moveCheck=request.form["moveCheck"],
    results = (
    db.session.query(
        Game.white_player_name,
        Game.black_player_name,
        Game.lichess_url,
        Game.opening,
        db.func.count('*').label('NumChecks')
    )
    .join(Moves, Game.lichess_url == Moves.lichess_url)
    .filter(
        Game.opening.like('%Sicilian Defense%'),
            or_(
                Moves.white_move.like('%+'),
                Moves.black_move.like('%+')
            )
    ).group_by(
        Game.white_player_name,
        Game.black_player_name,
        Game.lichess_url,
        Game.opening
    )
    .distinct()
    .all()
    )

    data = []
    for row in results:
        row_data = {
            "white_player_name": row.white_player_name,
            "black_player_name": row.black_player_name,
            "lichess_url": row.lichess_url,
            "opening": row.opening,
            "NumChecks": row.NumChecks
        }

        data.append(row_data)

    return jsonify(data)


if __name__ == "__main__":
    app.run()
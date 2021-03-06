import json
import sys

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.auth.models import Superusers
from app.board.forms import BoardForm
from app.board.models import Board, BoardPermission
from app.invite.models import Invite
from app.constants import *

# Define the blueprint: 'auth', set its url prefix: app.url/auth
mod_board = Blueprint('board', __name__, url_prefix='/board')


@mod_board.route('/create', methods=['POST'])
@jwt_required()
def create():

    current_user = json.loads(get_jwt_identity())

    form = BoardForm(request.form, meta={'csrf': False})

    with db.session.begin():

        try:

            # db.session.add(transaction)
            board = Board(name=form.board_name.data)
            db.session.add(board)

            db.session.flush()

            board_permission = BoardPermission(
                board_id=board.id, user_id=current_user['id'], permission=(1 << PERMISSION_ADMIN) + (1 << PERMISSION_OWNER))
            db.session.add(board_permission)

            board_id = board.id

            db.session.commit()

            return jsonify(board_id=board_id)

        except:
            db.session.rollback()

            _, error_message, _ = sys.exc_info()

            return jsonify(error=error_message)


@mod_board.route('/edit', methods=['POST'])
@jwt_required()
def edit():

    current_user = json.loads(get_jwt_identity())

    board_id = request.form.get('board_id')

    if not BoardPermission.has_permission(board_id, current_user['id']):
        return jsonify(error="No permission")

    form = BoardForm(request.form, meta={'csrf': False})

    board = Board.query.filter_by(id=board_id).one()

    board.name = form.board_name.data

    db.session.commit()

    return jsonify(board_name=board.name)


@mod_board.route('/front/<board_id>', methods=['GET'])
@jwt_required(optional=True)
def get_one(board_id):

    board = Board.query.filter_by(id=board_id).one()

    user = get_jwt_identity()

    if (user):

        user = json.loads(user)

        board_permission = BoardPermission.query.filter_by(
            board_id=board_id, user_id=user['id']).first()

        permission = board_permission.permission if board_permission else 0

        invite = Invite.query.filter_by(
            board_id=board_id, receiver_user_id=user['id'], status=INVITE_DEFAULT).first()

        invite_id = invite.id if invite else 0

        return jsonify(board_name=board.name, board_permission=permission, invite_id=invite_id)

    return jsonify(board_name=board.name)


@mod_board.route('/list', methods=['GET'])
@jwt_required(optional=True)
def board_list():

    board_list = Board.query.order_by(Board.group_id.asc()).limit(5).all()

    user = get_jwt_identity()

    permission = 0

    if (user):

        user = json.loads(user)

        superuser = Superusers.query.filter_by(user_id=user['id']).first()

        if superuser:
            permission = 1

    return jsonify(board_list=rows_dict(board_list), permission=permission)


@mod_board.route('/sort', methods=['POST'])
@jwt_required()
def board_sort():

    user = json.loads(get_jwt_identity())

    superuser = Superusers.query.filter_by(user_id=user['id']).first()

    if not superuser:
        return jsonify(error="No permission")

    sorted_group = json.loads(request.form.get('sorted_group'))

    group_id = [x['id'] for x in sorted_group]
    id_group_id = {int(x['id']): x['group_id'] for x in sorted_group}

    boards = Board.query.filter(Board.id.in_(group_id)).all()

    for b in boards:
        b.group_id = id_group_id[b.id]

    db.session.commit()

    return jsonify(status=1)

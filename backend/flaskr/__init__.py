import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category


QUESTIONS_PER_PAGE = 10
def paginate(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    cur_questions = questions[start:end]
    return cur_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    db = setup_db(app)
  
    # CORS(app, resource={r'/*': {'origins': '*'}})
    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Contect-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    '''
    endpoint to handle GET requests for all available categories.
    '''
    @app.route('/categories', methods=['GET'])
    def get_categories():
        try:
            data = Category.query.all()
            if len(data) == 0:
                abort(404)
            categories = {category.id: category.type for category in data}
            return jsonify({
                'success': True,
                'categories': categories,
                'total_categories': len(categories)
            })
        except:
            abort(400)
        finally:
            db.session.close()

    '''
    endpoint to handle GET requests for questions, including pagination (every 10 questions).  
    '''
    @app.route('/questions', methods=['GET'])
    def get_questions():
        try:
            selection = Question.query.order_by(Question.id).all()
            questions = paginate(request, selection)
            if len(questions) == 0:
                abort(404)
            current_category = [question['category'] for question in questions]

            data = Category.query.all()
            if len(data) == 0:
                abort(404)
            categories = {category.id:category.type for category in data}

            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(selection),
                'categories': categories,
                'current_category': current_category
            })
        except:
            abort(400)
        finally:
            db.session.close()

    '''
    endpoint to DELETE question using a question ID. 
    '''
    @app.route('/questions/<int:question_id>/delete', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()
            if question is None:
                abort(404)
            question.delete()
            questions = Question.query.order_by(Question.id).all()
            cur_questions = paginate(request, questions)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': cur_questions,
                'total_questions': len(questions)
            })
        except:
            abort(422)
        finally:
            db.session.close()    

    '''
    endpoint to POST a new question 
    '''
    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', 0)
        try:
            question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            cur_questions = paginate(request, selection)
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': cur_questions,
                'total_questions': len(selection)
            })
        except:
            abort(422)
        finally:
            db.session.close()


    '''
    a POST endpoint to get questions based on a search term. 
    '''
    @app.route('/questions/search', methods=['POST'])
    def search_question():
        data = request.get_json()
        item = data.get('searchTerm', None)
        if item is None: 
            abort(422)
        try:
            selection = Question.query.filter(Question.question.ilike('%{}%'.format(item))).all()
            questions = paginate(request, selection)
            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(selection),
                'current_category': None
            })
        except:
            abort(400)
        finally:
            db.session.close()

    '''
    GET endpoint to get questions based on category. 
    '''
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        try:
            category = Category.query.get(category_id).type
            data = Question.query.filter(Question.category == category_id).all()
            questions = paginate(request, data)
            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(data),
                'current_category': category
            })
        except:
            abort(400)
        finally:
            db.session.close()


    '''
    POST endpoint to get questions to play the quiz. 
    '''
    @app.route('/quizzes', methods=['POST'])
    def get_next_question():
        try:
            data = request.get_json()
            previous = data['previous_questions']
            category = data.get('quiz_category', None)
            if category is None or category['id'] == 0:
                questions = Question.query.filter(~Question.id.in_(previous)).all()
            else:
                questions = Question.query.filter(Question.category == category['id'], ~Question.id.in_(previous)).all()
            question = None if len(questions) == 0 else random.choice(questions).format()
            return jsonify({
                'success': True,
                'question': question
            })
        except:
            abort(400)
        finally:
            db.session.close()

    '''
    error handlers
    '''
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400
  
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404
  
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405
  
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable entity'
        }), 422
  
    return app

    
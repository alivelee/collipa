# coding: utf-8

import tornado.web

import config
from ._base import BaseHandler
from pony.orm import *

from models import Topic, Node
from forms import TopicForm, ReplyForm
from helpers import force_int

config = config.rec()

class HomeHandler(BaseHandler):
    @with_transaction
    def get(self, topic_id):
        topic_id = int(topic_id)
        page = force_int(self.get_argument('page', 0), 0)
        topic = Topic.get(id=topic_id)
        if not topic:
            raise tornado.web.HTTPError(404)
        action = self.get_argument('action', None)
        category = self.get_argument('category', None)
        user = self.current_user
        if action and user:
            if action == 'up':
                if topic.user_id != user.id:
                    result = user.up(topic_id=topic_id)
                else:
                    result = {'status': 'info', 'message':
                            '不能为自己的主题投票'}
            if action == 'down':
                if topic.user_id != user.id:
                    result = user.down(topic_id=topic_id)
                else:
                    result = {'status': 'info', 'message':
                            '不能为自己的主题投票'}
            if action == 'collect':
                result = user.collect(topic_id=topic_id)
            if action == 'thank':
                result = user.thank(topic_id=topic_id)
            if action == 'report':
                result = user.report(topic_id=topic_id)
            if self.is_ajax:
                return self.write(result)
            else:
                self.flash_message(result)
                return self.redirect_next_url()
        if not category:
            category = 'all'
        if category == 'all':
            reply_count = topic.reply_count
            url = topic.url
        elif category == 'hot':
            reply_count = count(topic.get_replies(page=None,
                    category=category))
            url = topic.url + '?category=hot'
        page_count = (reply_count + config.reply_paged - 1) // config.reply_paged
        if page == 0:
            page = page_count
        replies = topic.get_replies(page=page, category=category)
        form = ReplyForm()
        return self.render("topic/index.html", topic=topic, replies=replies, form=form,
                category=category, page=page, page_count=page_count, url=url)

class CreateHandler(BaseHandler):
    @with_transaction
    @tornado.web.authenticated
    def get(self):
        if not self.has_permission:
            return
        node_id = force_int(self.get_argument('node_id', 0), 0)
        node = Node.get(id=node_id)
        if node:
            selected = node.name
        else:
            selected = None
        choices = Node.get_node_choices()
        form = TopicForm.init(choices=choices, selected=selected)
        return self.render("topic/create.html", form=form, node=node)

    @with_transaction
    @tornado.web.authenticated
    def post(self):
        if not self.has_permission:
            return
        node_id = force_int(self.get_argument('node_id', 0), 0)
        node = Node.get(id=node_id)
        user = self.current_user
        form = TopicForm(self.request.arguments)
        if form.validate():
            topic = form.save(user=user)
            result = {'status': 'success', 'message': '主题创建成功',
                    'topic_url': topic.url}
            if self.is_ajax:
                return self.write(result)
            self.flash_message(result)
            return self.redirect(topic.url)
        if self.is_ajax:
            return self.write(form.result)
        return self.render("topic/create.html", form=form, node=node)

class EditHandler(BaseHandler):
    @with_transaction
    @tornado.web.authenticated
    def get(self, topic_id):
        if not self.has_permission:
            return
        topic = Topic.get(id=topic_id)
        if topic:
            selected = topic.node.name
        else:
            return self.redirect_next_url()
        choices = Node.get_node_choices()
        args = {'node_name': [selected], 'title': [topic.title], 'content':
                [topic.content]}
        form = TopicForm.init(choices=choices, selected=selected, args=args)
        return self.render("topic/create.html", form=form, node=topic.node)

    @with_transaction
    @tornado.web.authenticated
    def post(self, topic_id):
        if not self.has_permission:
            return
        topic = Topic.get(id=topic_id)
        if not topic:
            return self.redirect_next_url()
        user = self.current_user
        form = TopicForm(self.request.arguments)
        if form.validate():
            topic = form.save(user=user, topic=topic)
            result = {'status': 'success', 'message': '主题修改成功',
                    'topic_url': topic.url}
            if self.is_ajax:
                return self.write(result)
            self.flash_message(result)
            return self.redirect(topic.url)
        if self.is_ajax:
            return self.write(form.result)
        return self.render("topic/create.html", form=form, node=topic.node)

class HistoryHandler(BaseHandler):
    def get(self, topic_id):
        topic = Topic.get(id=topic_id)
        if not topic:
            return self.redirect_next_url()
        if not topic.histories:
            return self.redirect(topic.url)
        return self.render("topic/history.html", topic=topic, histories=topic.histories)

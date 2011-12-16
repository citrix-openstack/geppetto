'''
Created on 14 Jul 2011

@author: johngar
'''
from django import template


def is_quoted(str):
    return str[0] == str[-1] and str[0] in ('"', "'")


def do_welcome_item_title(parser, token):
    try:
        tag_name, id, title, status = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])
    if (not is_quoted(id)) or (not is_quoted(title)):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name)

    nodelist = parser.parse(("welcome-item-end",))
    parser.delete_first_token()

    return WelcomeTitleNode(id[1:-1], title[1:-1], status, nodelist)


class WelcomeTitleNode(template.Node):
    def __init__(self, id, title, status, content):
        self.id = id
        self.title = title
        self.status_variable = template.Variable(status)
        self.content = content

    def render(self, context):
        t = template.loader.get_template("ui/templatetags/welcome-item.html")

        try:
            status = self.status_variable.resolve(context)
        except template.VariableDoesNotExist:
            status = "none"

        data = {
                "id": self.id,
                "title": self.title,
                "status": status,
                "content": self.content.render(context)
                }
        return t.render(template.Context(data))

register = template.Library()
register.tag("welcome-item", do_welcome_item_title)

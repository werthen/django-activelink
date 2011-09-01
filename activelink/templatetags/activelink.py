from django.template import Library, Node, NodeList, VariableDoesNotExist
from django.core.urlresolvers import NoReverseMatch
from django.templatetags.future import url
from django.template.defaulttags import TemplateIfParser


register = Library()


class ActiveLinkNodeBase(Node):

    def __init__(self, urlnode, var, nodelist_true, nodelist_false):
        self.urlnode = urlnode
        self.var = var
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        try:
            var = self.urlnode.render(context)
        except NoReverseMatch:
            try:
                var = self.var.eval(context)
            except VariableDoesNotExist:
                var = None

        request = context['request']
        equal = self.is_active(request, var)

        if equal:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)


class ActiveLinkEqualNode(ActiveLinkNodeBase):

    def is_active(self, request, path_to_check):
        return path_to_check == request.get_full_path()


class ActiveLinkStartsWithNode(ActiveLinkNodeBase):

    def is_active(self, request, path_to_check):
        return request.get_full_path().startswith(path_to_check)


def parse(parser, token, end_tag):
    bits = token.split_contents()[1:]
    var = TemplateIfParser(parser, bits).parse()
    nodelist_true = parser.parse(('else', 'endifactive'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifactive',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()

    return var, nodelist_true, nodelist_false

@register.tag
def ifactive(parser, token):
    urlnode = url(parser, token)
    var, nodelist_true, nodelist_false = parse(parser, token, 'endifactive')
    return ActiveLinkEqualNode(urlnode, var, nodelist_true, nodelist_false)


@register.tag
def ifstartswith(parser, token):
    urlnode = url(parser, token)
    var, nodelist_true, nodelist_false = parse(parser, token, 'endifstartswith')
    return ActiveLinkStartsWithNode(urlnode, var, nodelist_true, nodelist_false)

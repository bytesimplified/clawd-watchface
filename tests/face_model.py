"""Small condition/visibility evaluator, not a Wear OS renderer."""
import ast
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'watchface/src/main/res'

def read_face():
    return ET.parse(RES / 'raw/watchface.xml').getroot()

def state(second=0, charging=False, battery=65):
    return {'SECOND': second % 60, 'MINUTE': second // 60 % 60,
            'HOUR_0_23': second // 3600 % 24, 'SECONDS_IN_DAY': second % 86400,
            'BATTERY_CHARGING_STATUS': charging, 'BATTERY_PERCENT': battery}

def evaluate(expression, values):
    expression = re.sub(r'\[([^]]+)\]', lambda m: repr(values[m[1]]), expression)
    expression = expression.replace('&&', ' and ').replace('||', ' or ')
    expression = re.sub(r'!(?!=)', ' not ', expression).strip()
    node = ast.parse(expression, mode='eval')
    allowed = (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.BinOp, ast.Compare,
               ast.Constant, ast.And, ast.Or, ast.Not, ast.Add, ast.Sub, ast.Mult,
               ast.Mod, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)
    if any(not isinstance(n, allowed) for n in ast.walk(node)):
        raise ValueError('Unsupported expression: ' + expression)
    return eval(compile(node, '<watchface-condition>', 'eval'), {'__builtins__': {}})

def visible(element, values, ambient=False):
    if element.tag == 'Group':
        alpha = element.get('alpha', '255')
        if ambient:
            for variant in element.findall('Variant'):
                if variant.get('target') == 'alpha':
                    alpha = variant.get('value')
        if alpha == '0':
            return []
    if element.tag == 'Condition':
        expressions = {n.get('name'): n.text for n in element.find('Expressions')}
        result = []
        for branch in element.findall('Compare'):
            if evaluate(expressions[branch.get('expression')], values):
                result += visible(branch, values, ambient)
        return result
    result = [element]
    for child in element:
        result += visible(child, values, ambient)
    return result

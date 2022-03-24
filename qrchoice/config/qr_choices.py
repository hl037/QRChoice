from . import common
from .tables import addTable

List = common.ExpressionParser.List
Group = common.ExpressionParser.Group
Call = common.ExpressionParser.Call

class TemplateParserError(RuntimeError):
  pass

def parseArity(arity):
  if '..' in arity :
    res = tuple( (float(int(s)) if (s := a.strip()) not in 'nN*' else float('+inf')) for a in arity.split('..') )
    if len(res) != 2 :
      raise common.ConfigSyntaxError('field arity should be one of `<number>`, `[n|N|*]`  or `<number>..[<number>|na|N|*]` where <number> is an integer number')
    return res
  else :
    if arity in 'nN*' :
      return (0., float('+inf'))
    else :
      a = float(int(arity))
      return a, a
  
class TemplateParser(common.ExpressionParser):
  list_delimiters = [(':', 0), (',', 1)]

  def parse(self, template_def):
    t = super().parse(template_def)
    match t :
      case (str() as cols) | List(',', cols) :
        pass
      case _  :
        raise TemplateParserError()
    qrch_fields = []
    for c in cols :
      match c :
        case List(':', (str() as fname, str() as arity)) :
          qrch_fields.append((fname, parseArity(arity)))
        case _ :
          raise TemplateParserError()
    return qrch_fields
    

def handler(c: common.Config, f):
  for sec, lines in common.parseSection(f) :
    template = []
    fields = []
    tname = sec
    for k, v in common.parseKeyValues(lines) :
        if k == 'template' :
          template.append(v)
        elif k == 'fields' :
          fields.append(v)
        else :
          raise common.ConfigUnknownKey(k)
    if not template :
      raise common.ConfigMissingKey('template')
    if not fields :
      raise common.ConfigMissingKey('fields')
    
    tp = TemplateParser()
    fields = ','.join(fields)
    template = ','.join(template)

    table = addTable(c, tname, fields)
    table._fields = fields
    table._template = template
    table.section = 'QRChoices'
    c.qrchoices[tname] = (table, tp.parse(template))

def to_file(c: common.Config, f):
  for tname in c._explicit_tables :
    table = c.tables[tname]
    if table.section == 'QRChoices' :
      f.write(f'[{tname}]\n')
      f.write(f'fields = {table._fields}\n')
      f.write(f'template = {table._template}\n\n')

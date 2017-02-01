from flask import Blueprint
from serviceweb.auth import only_for_editors
from serviceweb.forms import get_form
from restjson.client import objdict
from flask import request, redirect, g
from flask import render_template


edit = Blueprint('edit', __name__)


@edit.route("/<table_name>/<int:entry_id>/edit", methods=['GET', 'POST'])
@only_for_editors
def edit_table(table_name, entry_id):
    inline = request.args.get('inline')
    bust_cache = request.args.get('bust_cache')
    if request.method == 'POST':
        bust_cache = request.form.get('bust_cache', bust_cache)
    bust_cache = bust_cache is not None

    entry = g.db.get_entry(table_name, entry_id, bust_cache=bust_cache)
    form = get_form(table_name)(request.form, entry)
    from_ = request.args.get('from_', '/%s/%d' % (table_name, entry_id))

    if request.method == 'POST' and form.validate():
        form.populate_obj(entry)
        g.db.update_entry(table_name, entry)
        from_ = request.form.get('from_', from_)
        if bust_cache:
            from_ += '?bust_cache=1'
        return redirect(from_)

    action = 'Edit %r' % form.label(entry)
    backlink = '/%s/%d' % (table_name, entry_id)
    if inline is not None:
        tmpl = "inline_edit.html"
    else:
        tmpl = "edit.html"

    return render_template(tmpl, form=form, action=action, backlink=backlink,
                           form_action='/%s/%d/edit' % (table_name, entry_id),
                           from_=from_, bust_cache=bust_cache)


@edit.route("/<table_name>/<int:entry_id>/add_relation/<relname>/<target>",
            methods=['GET', 'POST'])
@only_for_editors
def add_relation(table_name, entry_id, relname, target):
    tmpl = "add_relation.html"
    relation = request.args.get('relation')
    entry = g.db.get_entry(table_name, entry_id)

    if relation:
        filters = [{'name': relation,
                    'op': 'eq',
                    'val': entry_id}]
        existing = g.db.get_entries(target, filters=filters)
    else:
        existing = g.db.get_entries(target)

    checked = [item['id'] for item in entry[relname]]
    for item in existing:
        item['checked'] = item['id'] in checked

    form = get_form(target)(request.form)
    action = '/%s/%d/add_relation/%s/%s' % (table_name, entry_id, relname,
                                            target)

    if relation:
        action += '?relation=%s' % relation

    if request.method == 'POST':
        if 'pick' in request.form:
            picked_entries = request.form.getlist('picked_entry')
            entry[relname] = [{'id': e} for e in picked_entries]
            # TODO check if changed
            g.db.update_entry(table_name, entry)
        else:
            # creation
            if form.validate():
                new_relation = objdict()
                form.populate_obj(new_relation)
                if relation:
                    new_relation[relation] = entry_id

                res = g.db.create_entry(target, new_relation)

                # XXX is that the best way ?
                entry[relname].append({'id': res.id})
                g.db.update_entry(table_name, entry)
                g.db.bust_cache(table_name, entry_id)

        return redirect('/%s/%d/edit' % (table_name, entry_id))

    return render_template(tmpl, form=form, form_action=action,
                           existing=existing, target=target)

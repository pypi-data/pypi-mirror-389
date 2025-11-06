<%inherit file="${context['main_template'].uri}" />
<%namespace file="/base/pager.mako" import="pager"/>
<%namespace file="/base/pager.mako" import="sortable"/>
<%namespace file="/base/searchformlayout.mako" import="searchform"/>

<%block name='content'>

${searchform()}

<div>
    <div>
        ${records.item_count} Résultat(s)
    </div>
    <div class='table_container'>
        <table class="hover_table">
            <thead>
                <tr>
                    <th scope="col" class="col_datetime">${sortable("Date", "created_at")}</th>
                    <th scope="col" class="col_text">${sortable("Action", "action_type")}</th>
                    <th scope="col" class="col_text">${sortable("Par", "user_login")}</th>
                    <th scope='col' class='col_text' title="Cette entrée a-t-elle été archivée ?">Archive</th>
                    <th scope="col" class="col_number">${sortable('Montant', 'amount')}</th>
                    <th scope="col" class="col_number">${sortable('TVA', 'tva_value')}</th>
                    <th scope="col" class="col_actions" title="Actions"><span class="screen-reader-text">Actions</span></th>
                </tr>
            </thead>
            <tbody>
                % if total is not UNDEFINED:
                    <tr class='row_recap'>
                        <th scope='row' colspan='4' class='col_text'>Total</th>
                        <td class='col_number'>${api.format_amount(total, precision=5)}&nbsp;€</td>
                        <td colspan='2'></td>
                    </tr>
                % endif

                % for item in records:
                    <tr>
                        <td class="col_datetime">${api.format_date(item.created_at)}</td>
                        <td class="col_text">
                        ${action_labels[item.action_type]}
                        </td>
                        <td class='col_text'>
                        ${item.user_login}
                        </td>
                        <td class='col_text'>
                            ${request.layout_manager.render_panel(archive_item_panel, context=item.endi_payment_archive_seal)}
                        </td>
                        <td class="col_number">
                            ${api.format_amount(item.amount, precision=5)}&nbsp;€
                        </td>
                        <td class="col_number">
                            ${api.format_amount(item.tva_value)} %
                        </td>
                         ${request.layout_manager.render_panel('action_buttons_td', links=stream_actions(item))}
                    </tr>
                % endfor
                    % if total is not UNDEFINED:
                        <tr class='row_recap'>
                            <th scope='row' colspan='4' class='col_text'>Total</th>
                            <td class='col_number'>${api.format_amount(total, precision=5)}&nbsp;€</td>
                            <td colspan='2'></td>
                        </tr>
                    % endif
                % if not records.item_count:
                    <td colspan="7" class="col_text"><em>Aucune entrée d'historique</em></td>
                % endif
            </tbody>
        </table>
    </div>
    ${pager(records)}
</div>
</%block>

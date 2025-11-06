<%inherit file="${context['main_template'].uri}" />

<%block name='content'>
    % if invoice.pdf_file_hash != history.invoice_pdf_file_hash:
    <div class='alert alert-danger'>
    Le PDF de la facture semble avoir été modifié après la saisie d'encaissement.
    </div>
    % endif
    <h3 class='highlight_title'>Action menée : ${action_labels[history.action_type]} d'un encaissement</h3>
    <div class='data_display'>
        Le ${api.format_datetime(history.created_at)} par ${history.user_login}.
    </div>

    % for panel in panels:
    ${request.layout_manager.render_panel(panel, context=history)}
    % endfor

    <div class='data_display separate_top'>
        <h2>Encaissement</h2>
        <div>
            <div class='layout flex two_cols'>
                <div><strong>Montant</strong></div>
                <div>${api.format_amount(history.amount, precision=5)}&nbsp;€</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>TVA</strong></div>
                <div>${api.format_amount(history.tva_value, precision=2)}&nbsp;%</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>Mode</strong></div>
                <div>${history.mode}</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>Compte CG banque</strong></div>
                <div>${history.bank_cg}</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>Identifiant de remise en banque</strong></div>
                <div>
                    % if history.bank_remittance_id:
                    ${history.bank_remittance_id}
                    % else:
                    <em>Non renseigné</em>
                    % endif
                </div>
            </div>
        </div>
    </div>
    <div class='data_display separate_top'>
        <h2>Facture</h2>
        <div>
            <div class='layout flex two_cols'>
                <div><strong>Numéro</strong></div>
                <div>${invoice.official_number}</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>Émise le</strong></div>
                <div>${api.format_short_date(invoice.date)}</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>HT</strong></div>
                <div>${api.format_amount(invoice.ht, precision=5)}&nbsp;€</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>TVA</strong></div>
                <div>${api.format_amount(invoice.tva, precision=5)}&nbsp;€</div>
            </div>
            <div class='layout flex two_cols'>
                <div><strong>TTC</strong></div>
                <div>${api.format_amount(invoice.ttc, precision=5)}&nbsp;€</div>
            </div>
            <a class='btn btn-default' href="${request.route_path('/invoices/{id}', id=invoice.id, _anchor='payment')}">
                Voir la facture
            </a>
        </div>
    </div>
</%block>

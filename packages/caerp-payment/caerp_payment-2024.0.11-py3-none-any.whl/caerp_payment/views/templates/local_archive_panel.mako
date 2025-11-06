<div class='data_display separate_top'>
    <h2>Archive</h2>
    % if archive_seal:
    <div>
        <div class='alert alert-info'>
        Lors de l'enregistrement de cette entrée du journal d'encaissement, une archive a été générée.<br />
        Une clé de certification de cette archive a été générée le ${api.format_short_date(archive_seal.created_at)}.
        </div>
        <div class='layout flex two_cols'>
            <div><strong>Type d'archive</strong></div>
            <div>${archive_type_label}</div>
        </div>
        % if file_link:
        <div class='layout flex two_cols'>
            <div><strong>Clé de certification associée au fichier</strong></div>
            <div>${archive_seal.remote_identification_key}</div>
        </div>
            <a href='${file_link}' class='btn btn-default' target='_blank'>
            ${api.icon('download')}
            Télécharger l'archive
            </a>
        % endif
        % if panels is not UNDEFINED:
        % for panel in panels:
        ${request.layout_manager.render_panel(panel, context=archive_seal)}
        % endfor
        % endif
    </div>
    % else:
    <em>Aucune scellée n'a été enregistrée pour cette entrée du journal</em>
    % endif
</div>

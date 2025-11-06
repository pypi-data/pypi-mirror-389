% if archive_seal:
    <span class='icon'>
    % if archive_seal.archive_type == 'local':
        ${api.icon('archive')}
    % else:
        ${api.icon('dispatch')}
    % endif
        ${archive_type_label}
        </span>
% else:
    <span class='icon'>${api.icon('close')}</span>
% endif

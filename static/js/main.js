$(function () {
  const $form      = $('#brief-form');
  const $submitBtn = $('#submit-btn');
  const $btnLabel  = $('.btn-label');
  const $btnSpinner= $('.btn-spinner');
  const $error     = $('#form-error');
  const $result    = $('#result-card');
  const $skeleton  = $('#skeleton-card');

  // ── Submit ──────────────────────────────────────────────
  $form.on('submit', function (e) {
    e.preventDefault();
    clearError();

    const brand    = $('#brand').val().trim();
    const platform = $('#platform').val();
    const goal     = $('#goal').val();
    const tone     = $('input[name="tone"]:checked').val();

    // Client-side validation
    if (!brand)    return showError('Please enter a brand name.');
    if (!platform) return showError('Please select a platform.');
    if (!goal)     return showError('Please select a campaign goal.');
    if (!tone)     return showError('Please choose a tone.');

    setLoading(true);
    $result.hide();
    $skeleton.show();

    $.ajax({
      url: '/api/generate/',
      method: 'POST',
      data: {
        csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
        brand,
        platform,
        goal,
        tone,
      },
      success: function (data) {
        renderResult(data);
      },
      error: function (xhr) {
        const msg = xhr.responseJSON?.error || 'Something went wrong. Please try again.';
        showError(msg);
      },
      complete: function () {
        setLoading(false);
        $skeleton.hide();
      },
    });
  });

  // ── Render result ───────────────────────────────────────
  function renderResult(data) {
    $('#result-brief').text(data.brief);

    const $angles = $('#result-angles').empty();
    data.angles.forEach(function (angle, i) {
      $('<li>').attr('data-n', i + 1).text(angle).appendTo($angles);
    });

    const $criteria = $('#result-criteria').empty();
    data.criteria.forEach(function (item) {
      $('<li>').text(item).appendTo($criteria);
    });

    const m = data.meta;
    $('#result-telemetry').html(
      chip('latency', m.latency_ms + ' ms') +
      chip('tokens', m.total_tokens.toLocaleString()) +
      chip('prompt', m.prompt_tokens + ' in') +
      chip('completion', m.completion_tokens + ' out')
    );

    const brand    = $('#brand').val().trim();
    const platform = $('#platform').val();
    const goal     = $('#goal').val();
    $('#result-meta').text(brand + ' · ' + platform + ' · ' + goal);

    $result.show();
    $('.layout').addClass('has-result');
  }

  function chip(label, value) {
    return '<span class="telemetry-chip">' + label + ': <span>' + value + '</span></span>';
  }

  // ── Loading state ───────────────────────────────────────
  function setLoading(loading) {
    $submitBtn.prop('disabled', loading);
    $btnLabel.toggle(!loading);
    $btnSpinner.toggle(loading);
    if (loading) {
      $('#brand').removeClass('error');
    }
  }

  // ── Error display ───────────────────────────────────────
  function showError(msg) {
    $error.text(msg).show();
  }
  function clearError() {
    $error.hide().text('');
  }

  // ── Copy to clipboard ───────────────────────────────────
  $('#copy-btn').on('click', function () {
    const brief    = $('#result-brief').text();
    const angles   = $('#result-angles li').map(function (i) {
      return (i + 1) + '. ' + $(this).text();
    }).get().join('\n');
    const criteria = $('#result-criteria li').map(function () {
      return '• ' + $(this).text();
    }).get().join('\n');

    const text = 'Brief:\n' + brief + '\n\nContent Angles:\n' + angles + '\n\nCreator Criteria:\n' + criteria;

    navigator.clipboard.writeText(text).then(function () {
      showToast('Copied to clipboard');
    });
  });

  // ── Toast ───────────────────────────────────────────────
  function showToast(msg) {
    const $t = $('<div class="toast">').text(msg).appendTo('body');
    setTimeout(function () { $t.addClass('show'); }, 10);
    setTimeout(function () {
      $t.removeClass('show');
      setTimeout(function () { $t.remove(); }, 300);
    }, 2200);
  }
});

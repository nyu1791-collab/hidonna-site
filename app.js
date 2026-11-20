/* =========================================================
   HIDONNA Live Portal — Scroll Float + Live Status + Resilience
   ========================================================= */

(() => {
  'use strict';

  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const KICK_SVG =
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">' +
    '<path d="M3 2h6v6h3V5h3V2h6v6h-3v3h-3v2h3v3h3v6h-6v-3h-3v-3H9v6H3V2z"/></svg>';

  /* ---------------------------------------------------------
     1. Scroll-Floating Typography
     --------------------------------------------------------- */
  function splitChars(el) {
    if (el.dataset.charDone) return;
    el.dataset.charDone = '1';
    let idx = 0;

    function walk(node) {
      const frag = document.createDocumentFragment();
      node.childNodes.forEach((child) => {
        if (child.nodeType === Node.TEXT_NODE) {
          Array.from(child.textContent || '').forEach((ch) => {
            const span = document.createElement('span');
            span.className = 'cf-char';
            span.style.setProperty('--ci', String(idx++));
            span.textContent = ch === ' ' ? '\u00A0' : ch;
            frag.appendChild(span);
          });
        } else if (child.nodeType === Node.ELEMENT_NODE) {
          const clone = child.cloneNode(false);
          clone.appendChild(walk(child));
          frag.appendChild(clone);
        }
      });
      return frag;
    }

    const built = walk(el);
    el.textContent = '';
    el.appendChild(built);
  }

  document.querySelectorAll('[data-char-float]').forEach(splitChars);

  const revealTargets = Array.from(
    document.querySelectorAll('.reveal-float, [data-char-float]:not([data-char-float="immediate"])')
  );

  function revealVisible() {
    const vh = window.innerHeight || 800;
    revealTargets.forEach((el) => {
      if (el.classList.contains('is-visible')) return;
      const r = el.getBoundingClientRect();
      if (r.top < vh * 0.94 && r.bottom > -20) {
        el.classList.add('is-visible');
      }
    });
  }

  requestAnimationFrame(() => {
    setTimeout(() => {
      document.querySelectorAll('[data-char-float="immediate"]').forEach((el) => el.classList.add('is-visible'));
      revealVisible();
    }, 40);
  });

  if (!prefersReduced && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) e.target.classList.add('is-visible');
        });
      },
      { threshold: 0.05 }
    );
    revealTargets.forEach((el) => io.observe(el));
  } else {
    revealTargets.forEach((el) => el.classList.add('is-visible'));
  }

  const progressBar = document.getElementById('scrollProgress');
  let ticking = false;
  function onScroll() {
    ticking = false;
    const sy = window.scrollY || 0;
    const vh = window.innerHeight || 800;
    const docH = Math.max(1, document.documentElement.scrollHeight - vh);
    if (progressBar) {
      progressBar.style.width = `${Math.min(100, (sy / docH) * 100).toFixed(2)}%`;
    }
    revealVisible();
  }
  window.addEventListener(
    'scroll',
    () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(onScroll);
      }
    },
    { passive: true }
  );
  onScroll();

  /* ---------------------------------------------------------
     2. Live Status (Kick / Whowatch / TwitCasting) & Latest 3 Renderer
     --------------------------------------------------------- */
  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function formatNumber(n) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return '';
    return Number(n).toLocaleString('ja-JP');
  }

  function applyPreviewOverride(data) {
    const mode = new URLSearchParams(window.location.search).get('preview');
    if (!mode) return data;
    const cloned = JSON.parse(JSON.stringify(data));
    if (mode === 'live-kick' || mode === 'live-both' || mode === 'live-all') {
      cloned.kick = Object.assign({}, cloned.kick, {
        is_live: true,
        title: '【テスト表示】Kick 深夜の街頭 IRL 外配信！',
        viewers: 428,
        category: 'IRL',
        thumbnail: './assets/banner.jpg',
        url: 'https://kick.com/hidonna',
      });
    }
    if (mode === 'live-who' || mode === 'live-both' || mode === 'live-all') {
      cloned.whowatch = Object.assign({}, cloned.whowatch, {
        is_live: true,
        title: '【テスト表示】ふわっち生配信！今夜も笑顔を咲かせます',
        viewers: 312,
        thumbnail: './assets/banner.jpg',
        url: 'https://whowatch.tv/profile/t:hid0nna',
      });
    }
    if (mode === 'live-tc' || mode === 'live-all') {
      cloned.twitcasting = Object.assign({}, cloned.twitcasting, {
        is_live: true,
        title: '【テスト表示】モイ！iPhoneからキャス配信中 -',
        viewers: 265,
        thumbnail: './assets/banner.jpg',
        url: 'https://twitcasting.tv/hid0nna',
      });
    }
    return cloned;
  }

  function applyLiveData(rawData) {
    if (!rawData) return;
    const data = applyPreviewOverride(rawData);
    const kick = data.kick || {};
    const who = data.whowatch || {};
    const tc = data.twitcasting || {};
    const yt = data.youtube || {};

    // --- Header Buttons & Hero Jump Pills (Full names + LIVE "pikkon-pikkon" pulse when online) ---
    const headerKickBtn = document.getElementById('headerKickBtn');
    const headerWhoBtn = document.getElementById('headerWhoBtn');
    const headerTcBtn = document.getElementById('headerTcBtn');
    const jumpKick = document.getElementById('jumpKick');
    const jumpWho = document.getElementById('jumpWho');
    const jumpTc = document.getElementById('jumpTc');

    if (headerKickBtn) {
      headerKickBtn.href = kick.url || 'https://kick.com/hidonna';
      headerKickBtn.classList.toggle('is-live-pulse', Boolean(kick.is_live));
      headerKickBtn.innerHTML = `${KICK_SVG}<span>Kick</span>${kick.is_live ? '<em class="hdr-live-chip">LIVE</em>' : ''}`;
    }

    if (headerWhoBtn) {
      headerWhoBtn.href = who.url || 'https://whowatch.tv/profile/t:hid0nna';
      headerWhoBtn.classList.toggle('is-live-pulse', Boolean(who.is_live));
      headerWhoBtn.innerHTML = `<img src="./assets/logo_whowatch.png" alt="ふわっち" /><span>ふわっち</span>${who.is_live ? '<em class="hdr-live-chip">LIVE</em>' : ''}`;
    }

    if (headerTcBtn) {
      headerTcBtn.href = tc.url || 'https://twitcasting.tv/hid0nna';
      headerTcBtn.classList.toggle('is-live-pulse', Boolean(tc.is_live));
      headerTcBtn.innerHTML = `<img src="./assets/logo_twitcasting.png" alt="ツイキャス" /><span>ツイキャス</span>${tc.is_live ? '<em class="hdr-live-chip">LIVE</em>' : ''}`;
    }

    if (jumpKick) {
      jumpKick.classList.toggle('is-live-pulse', Boolean(kick.is_live));
      jumpKick.innerHTML = kick.is_live ? 'Kick 配信 <em class="hdr-live-chip">LIVE</em>' : 'Kick 配信';
    }

    if (jumpWho) {
      jumpWho.classList.toggle('is-live-pulse', Boolean(who.is_live));
      jumpWho.innerHTML = who.is_live ? 'ふわっち <em class="hdr-live-chip">LIVE</em>' : 'ふわっち';
    }

    if (jumpTc) {
      jumpTc.classList.toggle('is-live-pulse', Boolean(tc.is_live));
      jumpTc.innerHTML = tc.is_live ? 'ツイキャス <em class="hdr-live-chip">LIVE</em>' : 'ツイキャス';
    }

    // --- Kick Frame ---
    const kickFrame = document.getElementById('kick-section');
    const kickBadge = document.getElementById('kickBadge');
    const kickDot = document.getElementById('kickDot');
    const kickBadgeText = document.getElementById('kickBadgeText');
    const kickFollowers = document.getElementById('kickFollowers');
    const kickTitle = document.getElementById('kickStreamTitle');
    const kickMeta = document.getElementById('kickStreamMeta');
    const kickCta = document.getElementById('kickCta');
    const kickThumbWrap = document.getElementById('kickThumbWrap');
    const kickThumbImg = document.getElementById('kickThumbImg');
    const kickAvatar = document.getElementById('kickAvatar');
    const kickProfileName = document.getElementById('kickProfileName');
    const kickProfileBio = document.getElementById('kickProfileBio');

    if (kickFollowers && kick.followers) {
      kickFollowers.textContent = `kick.com/hidonna ・ フォロワー ${formatNumber(kick.followers)}`;
    }
    if (kickAvatar && kick.avatar) {
      kickAvatar.onerror = () => {
        kickAvatar.onerror = null;
        kickAvatar.src = './assets/avatar_kick.webp';
      };
      kickAvatar.src = kick.avatar;
    }
    if (kickProfileName && kick.username) {
      kickProfileName.textContent = `${kick.username}（Kick プロフィール）`;
    }
    if (kickProfileBio && kick.bio) {
      kickProfileBio.textContent = kick.bio;
    }
    if (kickCta) {
      kickCta.href = kick.url || 'https://kick.com/hidonna';
    }

    if (kickFrame && kickBadge && kickDot && kickBadgeText && kickTitle && kickMeta && kickCta) {
      if (kick.is_live) {
        kickFrame.classList.add('is-live');
        kickBadge.className = 'live-badge on-kick';
        kickDot.className = 'pulse-dot live';
        kickBadgeText.textContent = 'LIVE 配信中';
        kickTitle.textContent = kick.title || 'Kick で生配信中！';
        const cat = kick.category ? ` ・ ${kick.category}` : '';
        kickMeta.textContent = `現在 ${formatNumber(kick.viewers)} 人が視聴中${cat}`;
        kickCta.innerHTML = '<span>今すぐ Kick ライブを見る</span><span aria-hidden="true">↗</span>';
        if (kickThumbWrap && kickThumbImg && kick.thumbnail) {
          kickThumbImg.onerror = () => {
            kickThumbWrap.classList.remove('show');
          };
          kickThumbImg.src = kick.thumbnail;
          kickThumbWrap.classList.add('show');
        } else if (kickThumbWrap && kickThumbImg) {
          kickThumbWrap.classList.remove('show');
          kickThumbImg.removeAttribute('src');
        }
      } else {
        kickFrame.classList.remove('is-live');
        kickBadge.className = 'live-badge';
        kickDot.className = 'pulse-dot';
        kickBadgeText.textContent = 'OFFLINE';
        kickTitle.textContent = '現在はオフラインです';
        kickMeta.textContent = '配信が始まると自動で「LIVE 配信中」＋視聴者数に切り替わります';
        kickCta.innerHTML = '<span>Kick チャンネルを開く</span><span aria-hidden="true">↗</span>';
        if (kickThumbWrap) kickThumbWrap.classList.remove('show');
        if (kickThumbImg) kickThumbImg.removeAttribute('src');
      }
    }

    // --- Kick Latest 3 VODs ---
    const kickVodGrid = document.getElementById('kickVodGrid');
    if (kickVodGrid && Array.isArray(kick.videos) && kick.videos.length > 0) {
      kickVodGrid.innerHTML = kick.videos
        .slice(0, 3)
        .map(
          (v, i) => `
          <a class="recent-card" href="${escapeHtml(v.url || 'https://kick.com/hidonna/videos')}" target="_blank" rel="noopener noreferrer">
            <div class="recent-thumb">
              <img src="${escapeHtml(v.thumbnail || './assets/avatar_kick.webp')}" alt="${escapeHtml(v.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='./assets/avatar_kick.webp';" />
              <span class="recent-tag-tl">KICK ${i + 1}</span>
              ${v.duration ? `<span class="recent-tag-br">${escapeHtml(v.duration)}</span>` : ''}
            </div>
            <div class="recent-body">
              <div class="recent-meta"><span>${escapeHtml(v.date || '')}</span><span>${escapeHtml(v.category || '')}</span></div>
              <div class="recent-title">${escapeHtml(v.title || 'Kick 過去配信')}</div>
            </div>
          </a>
        `
        )
        .join('');
    }

    // --- Whowatch Frame ---
    const whoFrame = document.getElementById('whowatch-section');
    const whoBadge = document.getElementById('whoBadge');
    const whoDot = document.getElementById('whoDot');
    const whoBadgeText = document.getElementById('whoBadgeText');
    const whoFollowers = document.getElementById('whoFollowers');
    const whoTitle = document.getElementById('whoStreamTitle');
    const whoMeta = document.getElementById('whoStreamMeta');
    const whoCta = document.getElementById('whoCta');
    const whoThumbWrap = document.getElementById('whoThumbWrap');
    const whoThumbImg = document.getElementById('whoThumbImg');
    const whoAvatar = document.getElementById('whoAvatar');
    const whoProfileName = document.getElementById('whoProfileName');
    const whoProfileBio = document.getElementById('whoProfileBio');

    if (whoCta) {
      whoCta.href = who.url || 'https://whowatch.tv/profile/t:hid0nna';
    }
    if (whoFollowers && who.followers) {
      whoFollowers.textContent = `${who.name || 'ヒドンナ@どやさ'} ・ フォロワー ${formatNumber(who.followers)}`;
    }
    if (whoAvatar && who.avatar) {
      whoAvatar.onerror = () => {
        whoAvatar.onerror = null;
        whoAvatar.src = './assets/avatar_whowatch.jpg';
      };
      whoAvatar.src = who.avatar;
    }
    if (whoProfileName && who.name) {
      whoProfileName.textContent = `${who.name}（ふわっちプロフィール）`;
    }
    if (whoProfileBio && who.bio) {
      whoProfileBio.textContent = who.bio;
    }

    if (whoFrame && whoBadge && whoDot && whoBadgeText && whoTitle && whoMeta && whoCta) {
      if (who.is_live) {
        whoFrame.classList.add('is-live');
        whoBadge.className = 'live-badge on-whowatch';
        whoDot.className = 'pulse-dot live';
        whoBadgeText.textContent = 'LIVE 配信中';
        whoTitle.textContent = who.title || 'ふわっちで生配信中！';
        whoMeta.textContent = who.viewers ? `現在 ${formatNumber(who.viewers)} 人が視聴中` : '今すぐ参加できます';
        whoCta.innerHTML = '<span>今すぐふわっちライブを見る</span><span aria-hidden="true">↗</span>';
        if (whoThumbWrap && whoThumbImg && who.thumbnail) {
          whoThumbImg.onerror = () => {
            whoThumbWrap.classList.remove('show');
          };
          whoThumbImg.src = who.thumbnail;
          whoThumbWrap.classList.add('show');
        } else if (whoThumbWrap && whoThumbImg) {
          whoThumbWrap.classList.remove('show');
          whoThumbImg.removeAttribute('src');
        }
      } else {
        whoFrame.classList.remove('is-live');
        whoBadge.className = 'live-badge';
        whoDot.className = 'pulse-dot';
        whoBadgeText.textContent = 'OFFLINE';
        whoTitle.textContent = '現在はオフラインです';
        whoMeta.textContent = '配信が始まると自動で「LIVE 配信中」＋視聴者数に切り替わります';
        whoCta.innerHTML = '<span>ふわっちを開く</span><span aria-hidden="true">↗</span>';
        if (whoThumbWrap) whoThumbWrap.classList.remove('show');
        if (whoThumbImg) whoThumbImg.removeAttribute('src');
      }
    }

    // --- Whowatch Latest 3 Archives ---
    const whoArchiveGrid = document.getElementById('whoArchiveGrid');
    if (whoArchiveGrid && Array.isArray(who.archives) && who.archives.length > 0) {
      whoArchiveGrid.innerHTML = who.archives
        .slice(0, 3)
        .map(
          (a, i) => `
          <a class="recent-card" href="${escapeHtml(a.url || 'https://whowatch.tv/profile/t:hid0nna')}" target="_blank" rel="noopener noreferrer">
            <div class="recent-thumb">
              <img src="${escapeHtml(a.thumbnail || './assets/avatar_whowatch.jpg')}" alt="${escapeHtml(a.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='./assets/avatar_whowatch.jpg';" />
              <span class="recent-tag-tl">ARCHIVE ${i + 1}</span>
              ${a.views ? `<span class="recent-tag-br">${formatNumber(a.views)} 視聴</span>` : (a.duration ? `<span class="recent-tag-br">${escapeHtml(a.duration)}</span>` : '')}
            </div>
            <div class="recent-body">
              <div class="recent-meta"><span>${escapeHtml(a.date || '')}</span>${a.duration ? `<span>${escapeHtml(a.duration)}</span>` : ''}</div>
              <div class="recent-title">${escapeHtml(a.title || 'ふわっち配信アーカイブ')}</div>
            </div>
          </a>
        `
        )
        .join('');
    }

    // --- TwitCasting Frame ---
    const tcFrame = document.getElementById('twitcasting-section');
    const tcBadge = document.getElementById('tcBadge');
    const tcDot = document.getElementById('tcDot');
    const tcBadgeText = document.getElementById('tcBadgeText');
    const tcFollowers = document.getElementById('tcFollowers');
    const tcTitle = document.getElementById('tcStreamTitle');
    const tcMeta = document.getElementById('tcStreamMeta');
    const tcCta = document.getElementById('tcCta');
    const tcThumbWrap = document.getElementById('tcThumbWrap');
    const tcThumbImg = document.getElementById('tcThumbImg');
    const tcAvatar = document.getElementById('tcAvatar');
    const tcProfileName = document.getElementById('tcProfileName');
    const tcProfileBio = document.getElementById('tcProfileBio');

    if (tcCta) {
      tcCta.href = tc.url || 'https://twitcasting.tv/hid0nna';
    }
    if (tcFollowers) {
      const supText = tc.supporters ? `サポーター ${tc.supporters}` : '';
      const lvText = tc.level ? `Lv.${tc.level}` : '';
      const metaBits = ['twitcasting.tv/hid0nna', supText, lvText].filter(Boolean);
      tcFollowers.textContent = metaBits.join(' ・ ');
    }
    if (tcAvatar && tc.avatar) {
      tcAvatar.onerror = () => {
        tcAvatar.onerror = null;
        tcAvatar.src = './assets/avatar_twitcasting.jpg';
      };
      tcAvatar.src = tc.avatar;
    }
    if (tcProfileName && tc.name) {
      tcProfileName.textContent = `${tc.name}（ツイキャスプロフィール）`;
    }
    if (tcProfileBio && tc.bio) {
      tcProfileBio.textContent = tc.bio;
    }

    if (tcFrame && tcBadge && tcDot && tcBadgeText && tcTitle && tcMeta && tcCta) {
      if (tc.is_live) {
        tcFrame.classList.add('is-live');
        tcBadge.className = 'live-badge on-twitcasting';
        tcDot.className = 'pulse-dot live-tc';
        tcBadgeText.textContent = 'LIVE 配信中';
        tcTitle.textContent = tc.title || 'ツイキャスで生配信中！';
        tcMeta.textContent = tc.viewers ? `現在 ${formatNumber(tc.viewers)} 人が視聴中` : '今すぐ参加できます';
        tcCta.innerHTML = '<span>今すぐツイキャスを見る</span><span aria-hidden="true">↗</span>';
        if (tcThumbWrap && tcThumbImg && tc.thumbnail) {
          tcThumbImg.onerror = () => {
            tcThumbWrap.classList.remove('show');
          };
          tcThumbImg.src = tc.thumbnail;
          tcThumbWrap.classList.add('show');
        } else if (tcThumbWrap && tcThumbImg) {
          tcThumbWrap.classList.remove('show');
          tcThumbImg.removeAttribute('src');
        }
      } else {
        tcFrame.classList.remove('is-live');
        tcBadge.className = 'live-badge';
        tcDot.className = 'pulse-dot';
        tcBadgeText.textContent = 'OFFLINE';
        tcTitle.textContent = '現在はオフラインです';
        tcMeta.textContent = '配信が始まると自動で「LIVE 配信中」に切り替わります';
        tcCta.innerHTML = '<span>ツイキャスを開く</span><span aria-hidden="true">↗</span>';
        if (tcThumbWrap) tcThumbWrap.classList.remove('show');
        if (tcThumbImg) tcThumbImg.removeAttribute('src');
      }
    }

    // --- TwitCasting Latest 3 Recorded Movies ---
    const tcMovieGrid = document.getElementById('tcMovieGrid');
    if (tcMovieGrid && Array.isArray(tc.movies) && tc.movies.length > 0) {
      tcMovieGrid.innerHTML = tc.movies
        .slice(0, 3)
        .map(
          (m, i) => `
          <a class="recent-card" href="${escapeHtml(m.url || 'https://twitcasting.tv/hid0nna/show/')}" target="_blank" rel="noopener noreferrer">
            <div class="recent-thumb">
              <img src="${escapeHtml(m.thumbnail || './assets/avatar_twitcasting.jpg')}" alt="${escapeHtml(m.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='./assets/avatar_twitcasting.jpg';" />
              <span class="recent-tag-tl">CAS ${i + 1}</span>
              ${m.views ? `<span class="recent-tag-br">${formatNumber(m.views)} 視聴</span>` : (m.duration ? `<span class="recent-tag-br">${escapeHtml(m.duration)}</span>` : '')}
            </div>
            <div class="recent-body">
              <div class="recent-meta"><span>${escapeHtml(m.date || '')}</span>${m.duration ? `<span>${escapeHtml(m.duration)}</span>` : ''}</div>
              <div class="recent-title">${escapeHtml(m.title || 'ツイキャス配信アーカイブ')}</div>
            </div>
          </a>
        `
        )
        .join('');
    }

    // --- X Latest 3 Posts ---
    const xData = data.x || {};
    const xPostGrid = document.getElementById('xPostGrid');
    if (xPostGrid && Array.isArray(xData.posts) && xData.posts.length > 0) {
      xPostGrid.innerHTML = xData.posts
        .slice(0, 3)
        .map(
          (p, i) => `
          <a class="recent-card" href="${escapeHtml(p.url || 'https://x.com/hid0nna')}" target="_blank" rel="noopener noreferrer">
            <div class="recent-thumb">
              <img src="${escapeHtml(p.image || './assets/banner.jpg')}" alt="${escapeHtml(p.text || 'X ポスト')}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='./assets/banner.jpg';" />
              <span class="recent-tag-tl">POST ${i + 1}</span>
            </div>
            <div class="recent-body">
              <div class="recent-meta"><span>${escapeHtml(p.date || '')}</span></div>
              <div class="recent-title">${escapeHtml(p.text || '')}</div>
              <div class="x-stats">
                ${p.likes !== undefined ? `<span>♥ ${formatNumber(p.likes)}</span>` : ''}
                ${p.reposts !== undefined ? `<span>↻ ${formatNumber(p.reposts)}</span>` : ''}
                ${p.views !== undefined ? `<span>👁 ${formatNumber(p.views)}</span>` : ''}
              </div>
            </div>
          </a>
        `
        )
        .join('');
    }

    // --- YouTube Latest 3 Regular Videos ---
    const ytGrid = document.getElementById('ytGrid');
    if (ytGrid && Array.isArray(yt.videos) && yt.videos.length > 0) {
      ytGrid.innerHTML = yt.videos
        .slice(0, 3)
        .map(
          (v, i) => `
          <a class="yt-card reveal-float is-visible" href="${escapeHtml(v.url)}" target="_blank" rel="noopener noreferrer">
            <div class="yt-thumb-wrap">
              <img src="${escapeHtml(v.thumbnail)}" alt="${escapeHtml(v.title)}" loading="lazy" referrerpolicy="no-referrer" onerror="this.onerror=null;this.src='./assets/banner.jpg';" />
              <span class="yt-new-tag">NEW ${i + 1}</span>
              <div class="yt-play-badge">
                <span class="yt-play-btn">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="#fff"><path d="M8 5v14l11-7z"/></svg>
                </span>
              </div>
            </div>
            <div class="yt-info">
              <span class="yt-date">${escapeHtml(v.published)}</span>
              <h3 class="yt-title">${escapeHtml(v.title)}</h3>
            </div>
          </a>
        `
        )
        .join('');
    }

    const updatedEl = document.getElementById('lastUpdated');
    if (updatedEl && data.fetched_at) {
      updatedEl.textContent = `最終確認：${data.fetched_at}（60秒ごとに自動更新）`;
    }
  }

  let isFetching = false;
  let lastFetchAt = 0;
  let useStaticJson = window.location.hostname.endsWith('.github.io');

  async function fetchLiveStatus(force = false) {
    if (window.location.protocol === 'file:') return;
    if (isFetching) return;
    isFetching = true;
    const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
    const timer = controller ? setTimeout(() => controller.abort(), 12000) : null;
    try {
      let res = null;
      if (!useStaticJson) {
        res = await fetch(`/api/live-status${force ? '?refresh=1' : ''}`, {
          cache: 'no-store',
          signal: controller ? controller.signal : undefined,
        });
        if (!res.ok) {
          useStaticJson = true;
          res = null;
        }
      }
      if (!res) {
        res = await fetch(`./live-status.json?t=${Date.now()}`, {
          cache: 'no-store',
          signal: controller ? controller.signal : undefined,
        });
      }
      if (res && res.ok) {
        const data = await res.json();
        applyLiveData(data);
        lastFetchAt = Date.now();
      }
    } catch {
      // 一時的な通信エラー時でも画面を壊さず現在の表示を維持
    } finally {
      if (timer) clearTimeout(timer);
      isFetching = false;
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && Date.now() - lastFetchAt > 20000) {
      fetchLiveStatus(false);
    }
  });

  fetchLiveStatus(false);
  setInterval(() => fetchLiveStatus(false), 60000);
})();

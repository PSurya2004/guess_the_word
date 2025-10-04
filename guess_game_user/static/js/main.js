document.addEventListener('DOMContentLoaded', () => {
  const API_PREFIX = '/guess_game_user/api';

  // State
  let guessedWords = [[]];
  let availableSpace = 1; // tile id starts at 1
  let guessedWordCount = 0; // number of guesses already submitted
  let sessionActive = true;

  const keys = document.querySelectorAll('.keyboard-row button');

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function startNewSession() {
    return fetch(API_PREFIX + '/new-session/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: JSON.stringify({}),
    }).then(async res => {
      const ct = res.headers.get('content-type') || '';
      let data = {};
      if (ct.indexOf('application/json') !== -1) {
        data = await res.json();
      }
      if (data && data.session_started) sessionActive = true; else sessionActive = false;
      return data;
    }).catch(err => {
      console.warn('Failed to start session', err);
      sessionActive = false;
      return { session_started: false, message: 'Failed to start session' };
    });
  }

  function createSquares() {
    const gameBoard = document.getElementById('board');
    // 5 guesses x 5 letters = 25 tiles
    for (let i = 0; i < 25; i++) {
      const square = document.createElement('div');
      square.classList.add('square');
      square.classList.add('animate__animated');
      square.setAttribute('id', String(i + 1));
      gameBoard.appendChild(square);
    }
  }

  function getCurrentWordArr() {
    return guessedWords[guessedWords.length - 1];
  }

  function updateGuessedWords(letter) {
    const currentWordArr = getCurrentWordArr();
    if (currentWordArr && currentWordArr.length < 5) {
      currentWordArr.push(letter);
      const availableSpaceEl = document.getElementById(String(availableSpace));
      availableSpaceEl.textContent = letter;
      availableSpace = availableSpace + 1;
    }
  }

  function handleDeleteLetter() {
    const currentWordArr = getCurrentWordArr();
    if (!currentWordArr || currentWordArr.length === 0) return;
    currentWordArr.pop();
    guessedWords[guessedWords.length - 1] = currentWordArr;
    const lastLetterEl = document.getElementById(String(availableSpace - 1));
    if (lastLetterEl) lastLetterEl.textContent = '';
    availableSpace = Math.max(1, availableSpace - 1);
  }

  function colorFromCode(code) {
    if (code === 2) return 'rgb(83, 141, 78)';
    if (code === 1) return 'rgb(181, 159, 59)';
    return 'rgb(58, 58, 60)';
  }

  async function handleSubmitWord() {
    if (!sessionActive) {
      if (window.confirm('No active session. Start a new game now?')) {
        const result = await startNewSession();
        if (!result || !result.session_started) {
          window.alert(result && result.message ? result.message : 'Could not start a new session.');
          return;
        }
      } else {
        return;
      }
    }

    const currentWordArr = getCurrentWordArr();
    if (!currentWordArr || currentWordArr.length !== 5) {
      window.alert('Word must be 5 letters');
      return;
    }

    const currentWord = currentWordArr.join('').toUpperCase();

    try {
      const res = await fetch(API_PREFIX + '/guess/', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ guessed_word: currentWord }),
      });

      if (!res.ok) {
        let err = {};
        try { err = await res.json(); } catch (e) { /* non-json */ }
        window.alert(err.message || `Unable to submit guess (status ${res.status})`);
        return;
      }

      const data = await res.json();
      const firstLetterId = guessedWordCount * 5 + 1;
      const interval = 200;

      currentWordArr.forEach((letter, index) => {
        setTimeout(() => {
          const tileColor = colorFromCode(data.colors[index]);
          const letterId = firstLetterId + index;
          const letterEl = document.getElementById(String(letterId));
          if (letterEl) {
            letterEl.classList.add('animate__flipInX');
            letterEl.style = `background-color:${tileColor};border-color:${tileColor}`;
            letterEl.textContent = currentWord[index];
          }
        }, interval * index);
      });

      guessedWordCount += 1;

      if (data.is_correct) {
        sessionActive = false;
        setTimeout(() => {
          if (window.confirm('Congratulations! You guessed the word. Click OK to finish.')) {
            window.location.reload();
          }
        }, 500);
        return;
      }

      if (data.guesses_left <= 0) {
        sessionActive = false;
        setTimeout(() => {
          if (window.confirm(`Better luck next time! The word was ${data.target_word}. Click OK to finish.`)) {
            window.location.reload();
          }
        }, 500);
        return;
      }

      guessedWords.push([]);
    } catch (e) {
      console.error(e);
      window.alert('Network error submitting guess');
    }
  }

  // Initialize board and keyboard handlers
  createSquares();

  for (let i = 0; i < keys.length; i++) {
    keys[i].onclick = ({ target }) => {
      const letter = target.getAttribute('data-key');
      if (letter === 'enter') { handleSubmitWord(); return; }
      if (letter === 'del') { handleDeleteLetter(); return; }
      const ch = letter.toUpperCase();
      if (/^[A-Z]$/.test(ch)) {
        updateGuessedWords(ch);
        const availableSpaceEl = document.getElementById(String(availableSpace - 1));
        if (availableSpaceEl) availableSpaceEl.textContent = ch;
      }
    };
  }

  // Try to start a session on load
  startNewSession().then(data => {
    if (data && data.message && !data.session_started) {
      sessionActive = false;
      // note: avoid noisy alert on load; let submit attempt prompt user
      console.warn('New session not started:', data.message);
    }
  }).catch(err => console.warn('Could not start session', err));
});

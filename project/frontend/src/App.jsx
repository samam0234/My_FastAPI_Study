import { useEffect, useState } from "react";
import { api } from "./api";

const TITLE = "Mini Board";

function useAuth() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem("auth");
    return saved ? JSON.parse(saved) : null;
  });

  const login = (user, token) => {
    const next = { id: user.id, email: user.email, nickname: user.nickname, token };
    localStorage.setItem("auth", JSON.stringify(next));
    setAuth(next);
  };

  const logout = async () => {
    if (auth?.token) {
      try {
        await api.logout(auth.token);
      } catch {
        // 서버가 토큰을 이미 버렸어도 화면의 로그인 상태는 지운다.
      }
    }
    localStorage.removeItem("auth");
    setAuth(null);
  };

  return { auth, login, logout };
}

function AuthForm({ onLogin, onError }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nickname, setNickname] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    onError("");
    try {
      if (mode === "signup") {
        await api.signup(email, password, nickname);
      }
      const logged = await api.login(email, password);
      onLogin(logged.data.user, logged.data.accessToken);
    } catch (err) {
      onError(err.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>{mode === "login" ? "로그인" : "회원가입"}</h2>
      {mode === "signup" && (
        <input placeholder="닉네임" value={nickname} onChange={(e) => setNickname(e.target.value)} required />
      )}
      <input type="email" placeholder="이메일" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <input
        type="password"
        placeholder="비밀번호 8자 이상"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit" disabled={pending}>
        {pending ? "처리 중..." : mode === "login" ? "로그인" : "가입하고 로그인"}
      </button>
      <button type="button" className="link" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
        {mode === "login" ? "계정이 없나요? 회원가입" : "이미 계정이 있나요? 로그인"}
      </button>
    </form>
  );
}

function PostForm({ token, onCreated, onError }) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (pending) return;
    setPending(true);
    onError("");
    try {
      const parsedTags = tags.split(",").map((tag) => tag.trim()).filter(Boolean);
      await api.createPost({ title, body, tags: parsedTags }, token);
      setTitle("");
      setBody("");
      setTags("");
      onCreated();
    } catch (err) {
      onError(err.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>새 글</h2>
      <input placeholder="제목" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <textarea placeholder="본문" value={body} onChange={(e) => setBody(e.target.value)} required />
      <input placeholder="태그, 쉼표로 구분" value={tags} onChange={(e) => setTags(e.target.value)} />
      <button type="submit" disabled={pending}>
        {pending ? "저장 중..." : "등록"}
      </button>
    </form>
  );
}

function PostList({ posts, auth, onChanged, onError }) {
  const [comment, setComment] = useState("");

  async function handleDelete(id) {
    onError("");
    try {
      await api.deletePost(id, auth.token);
      onChanged();
    } catch (err) {
      onError(err.message);
    }
  }

  async function handleComment(event, id) {
    event.preventDefault();
    onError("");
    try {
      await api.addComment(id, comment, auth.token);
      setComment("");
      onChanged();
    } catch (err) {
      onError(err.message);
    }
  }

  return (
    <ul className="posts">
      {posts.map((post) => (
        <li key={post.id} className="card">
          <div className="post-header">
            <strong>{post.title}</strong>
            <span className="badge">댓글 {post.commentCount}</span>
          </div>
          <p>{post.body}</p>
          <small>{post.author ? post.author.nickname : "작성자 없음"} · {post.createdAt}</small>
          {auth && post.author?.id === auth.id && (
            <button className="danger" onClick={() => handleDelete(post.id)}>
              삭제
            </button>
          )}
          {auth && (
            <form onSubmit={(event) => handleComment(event, post.id)}>
              <input placeholder="댓글" value={comment} onChange={(e) => setComment(e.target.value)} />
            </form>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function App() {
  const { auth, login, logout } = useAuth();
  const [posts, setPosts] = useState([]);
  const [meta, setMeta] = useState({ page: 1, total: 0, totalPages: 0 });
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");

  async function loadPosts(nextPage = page, nextQ = q) {
    try {
      const data = await api.listPosts({ page: String(nextPage), limit: "10", q: nextQ });
      setPosts(data.data);
      setMeta(data.meta);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadPosts(page, q);
  }, [page]);

  return (
    <main>
      <header className="topbar">
        <h1>{TITLE}</h1>
        {auth ? (
          <div>
            <span>{auth.nickname}님</span>
            <button onClick={logout}>로그아웃</button>
          </div>
        ) : null}
      </header>
      {error && <p className="error">{error}</p>}
      {!auth && <AuthForm onLogin={login} onError={setError} />}
      {auth && <PostForm token={auth.token} onCreated={() => loadPosts(1, q)} onError={setError} />}
      <form
        className="card"
        onSubmit={(event) => {
          event.preventDefault();
          setPage(1);
          loadPosts(1, q);
        }}
      >
        <input placeholder="제목·본문 검색" value={q} onChange={(e) => setQ(e.target.value)} />
        <button type="submit">검색</button>
      </form>
      <h2>게시글 {meta.total}건</h2>
      <PostList posts={posts} auth={auth} onChanged={() => loadPosts(page, q)} onError={setError} />
      <div className="topbar">
        <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          이전
        </button>
        <span>
          {meta.page} / {meta.totalPages || 1}
        </span>
        <button
          type="button"
          disabled={meta.totalPages === 0 || page >= meta.totalPages}
          onClick={() => setPage((value) => value + 1)}
        >
          다음
        </button>
      </div>
    </main>
  );
}

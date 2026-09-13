import { useEffect, useState } from "react";
import { api } from "./api";

function useAuth() {
  const [auth, setAuth] = useState(() => {
    const saved = localStorage.getItem("auth");
    return saved ? JSON.parse(saved) : null;
  });

  const login = (username, token) => {
    const next = { username, token };
    localStorage.setItem("auth", JSON.stringify(next));
    setAuth(next);
  };

  const logout = () => {
    localStorage.removeItem("auth");
    setAuth(null);
  };

  return { auth, login, logout };
}

function AuthForm({ onLogin, onError }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setPending(true);
    onError("");
    try {
      if (mode === "register") {
        await api.register(username, password);
      }
      const token = await api.login(username, password);
      onLogin(username, token.access_token);
      setUsername("");
      setPassword("");
    } catch (err) {
      onError(err.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>{mode === "login" ? "로그인" : "회원가입 후 로그인"}</h2>
      <input
        placeholder="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <input
        placeholder="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit" disabled={pending}>
        {mode === "login" ? "로그인" : "회원가입 + 로그인"}
      </button>
      <button
        type="button"
        className="link"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
      >
        {mode === "login" ? "계정이 없나요? 회원가입" : "이미 계정이 있나요? 로그인"}
      </button>
    </form>
  );
}

function PostForm({ token, onCreated, onError }) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [published, setPublished] = useState(true);
  const [pending, setPending] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setPending(true);
    onError("");
    try {
      await api.createPost({ title, content, published }, token);
      setTitle("");
      setContent("");
      setPublished(true);
      onCreated();
    } catch (err) {
      onError(err.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2>새 글 작성</h2>
      <input placeholder="제목" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <textarea placeholder="내용" value={content} onChange={(e) => setContent(e.target.value)} required />
      <label>
        <input type="checkbox" checked={published} onChange={(e) => setPublished(e.target.checked)} />
        공개
      </label>
      <button type="submit" disabled={pending}>
        작성
      </button>
    </form>
  );
}

function PostList({ posts, auth, onDeleted, onError }) {
  async function handleDelete(id) {
    onError("");
    try {
      await api.deletePost(id, auth.token);
      onDeleted();
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
            {!post.published && <span className="badge">비공개</span>}
          </div>
          <p>{post.content}</p>
          {auth && (
            <button className="danger" onClick={() => handleDelete(post.id)}>
              삭제
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}

export default function App() {
  const { auth, login, logout } = useAuth();
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");

  async function loadPosts() {
    try {
      const data = await api.listPosts();
      setPosts(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadPosts();
  }, []);

  return (
    <main>
      <header className="topbar">
        <h1>Mini Board</h1>
        {auth ? (
          <div>
            <span>{auth.username}님 환영합니다</span>
            <button onClick={logout}>로그아웃</button>
          </div>
        ) : null}
      </header>

      {error && <p className="error">{error}</p>}

      {!auth && <AuthForm onLogin={login} onError={setError} />}
      {auth && <PostForm token={auth.token} onCreated={loadPosts} onError={setError} />}

      <h2>게시글 목록 ({total})</h2>
      <PostList posts={posts} auth={auth} onDeleted={loadPosts} onError={setError} />
    </main>
  );
}

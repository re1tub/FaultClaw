import { Link, useLocation } from 'react-router-dom';

export default function NavBar() {
  const { pathname } = useLocation();
  const active = (path) =>
    path === '/' ? pathname === '/' : pathname.startsWith(path);

  return (
    <nav className="navbar">
      <div className="container">
        <Link to="/" className="nav-logo">
          <span className="nav-logo-bracket">[</span>
          <span className="nav-logo-word">FAULT</span>
          <span className="nav-logo-accent">CLAW</span>
          <span className="nav-logo-bracket">]</span>
        </Link>
        <div className="nav-links">
          <Link to="/" className={`nav-link${active('/') ? ' active' : ''}`}>Home</Link>
          <Link to="/dashboard" className={`nav-link${active('/dashboard') ? ' active' : ''}`}>Dashboard</Link>
          <Link to="/docs" className={`nav-link${active('/docs') ? ' active' : ''}`}>API Docs</Link>
          <Link to="/dashboard" className="nav-link-cta">Open App →</Link>
        </div>
      </div>
    </nav>
  );
}

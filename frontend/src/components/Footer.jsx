import { TELEFONO_WHATSAPP, TELEFONO_VISIBLE } from "../contacto";

function IconoWhatsApp() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M12 2a10 10 0 0 0-8.6 15L2 22l5.2-1.4A10 10 0 1 0 12 2Zm5.7 14.2c-.2.6-1.3 1.2-1.9 1.3-.5.1-1.1.1-1.8-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5.1-4.5-.1-.2-1.2-1.6-1.2-3 0-1.4.7-2.1 1-2.4.3-.3.6-.3.8-.3h.6c.2 0 .4 0 .6.5.2.5.7 1.8.8 1.9.1.2.1.3 0 .5-.1.2-.2.3-.3.5-.2.2-.3.3-.1.6.2.3.9 1.4 1.9 2.3 1.3 1.1 2.3 1.5 2.6 1.6.3.1.5.1.7-.1.2-.2.8-.9 1-1.2.2-.3.4-.2.7-.1.3.1 1.8.9 2.1 1 .3.2.5.2.6.3.1.2.1.9-.1 1.5Z"
        fill="currentColor"
      />
    </svg>
  );
}

function IconoInstagram() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="3" y="3" width="18" height="18" rx="5" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="12" cy="12" r="4.2" stroke="currentColor" strokeWidth="1.6" />
      <circle cx="17.2" cy="6.8" r="1.1" fill="currentColor" />
    </svg>
  );
}

export default function Footer() {
  return (
    <footer className="pie" id="contacto">
      <span>© Kukis {new Date().getFullYear()}</span>
      <div className="grupo">
        <span className="logo">
          <span className="logo-marca">K</span>
          <span>Kukis</span>
        </span>
        <a href="https://instagram.com/kukis" target="_blank" rel="noreferrer">
          <IconoInstagram />
          @kukis
        </a>
        <a
          href={`https://wa.me/${TELEFONO_WHATSAPP}`}
          target="_blank"
          rel="noreferrer"
          aria-label={`Escríbenos por WhatsApp al ${TELEFONO_VISIBLE}`}
          title={`WhatsApp: ${TELEFONO_VISIBLE}`}
        >
          <IconoWhatsApp />
        </a>
      </div>
    </footer>
  );
}

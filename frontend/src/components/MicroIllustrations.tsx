/** 5 micro-illustrations 24px — secteur avicole sans cliché (INC-15) */
export function IconFerme(props: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden className={props.className}>
      <path d="M3 10 L12 3 L21 10" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round" />
      <path d="M6 10 V19 H18 V10" stroke="currentColor" strokeWidth="1.3" />
      <path d="M9 19 V13 H15 V19" stroke="currentColor" strokeWidth="1.2" />
      <circle cx="12" cy="8" r="1" fill="currentColor" opacity="0.9" />
    </svg>
  )
}
export function IconMedia(props: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden className={props.className}>
      <rect x="3" y="6" width="14" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M17 9 L21 7 V15 L17 13" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <circle cx="8" cy="11" r="1" fill="currentColor" />
    </svg>
  )
}
export function IconAcademy(props: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden className={props.className}>
      <path d="M4 7 L12 11 L20 7" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
      <path d="M4 7 V12 L12 16 L20 12 V7" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round" />
      <path d="M12 11 V16" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  )
}
export function IconClub(props: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden className={props.className}>
      <circle cx="12" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.3" />
      <path d="M5 19 C5 14.5 8 13 12 13 C16 13 19 14.5 19 19" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
      <circle cx="12" cy="8" r="1" fill="currentColor" opacity="0.8" />
    </svg>
  )
}
export function IconQR(props: { className?: string }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden className={props.className}>
      <rect x="3" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="14" y="3" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="3" y="14" width="7" height="7" rx="1" stroke="currentColor" strokeWidth="1.3" />
      <rect x="14" y="14" width="3" height="3" rx="0.5" fill="currentColor" />
      <rect x="18" y="14" width="3" height="3" rx="0.5" fill="currentColor" opacity="0.7" />
      <rect x="14" y="18" width="3" height="3" rx="0.5" fill="currentColor" opacity="0.7" />
    </svg>
  )
}

export const ECO_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Ferme Expérience': IconFerme,
  'Media Partnership': IconMedia,
  'DABA Academy': IconAcademy,
  'DABA Club': IconClub,
  'QR Code Marketing': IconQR,
}

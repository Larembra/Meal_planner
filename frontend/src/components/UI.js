import React from 'react'

const fallbackImage = '/static/vitya_nyam_nyam.jpg'

export function Button({ children, href, variant = 'primary', className = '', ...props }) {
  const cn = `button ${variant} ${className}`
  return href ? <a href={href} className={cn}>{children}</a> : <button type="button" className={cn} {...props}>{children}</button>
}

export function ImageBox({ src, alt = '', className = '' }) {
  const [currentSrc, setCurrentSrc] = React.useState(src || fallbackImage)

  React.useEffect(() => {
    setCurrentSrc(src || fallbackImage)
  }, [src])

  return <div className={`image-box ${className}`}>
    <img
      src={currentSrc}
      alt={alt}
      onError={() => {
        if (currentSrc !== fallbackImage) setCurrentSrc(fallbackImage)
      }}
    />
  </div>
}


export function Card({ children, className = '', ...props }) {
  return <div className={`card ${className}`} {...props}>{children}</div>
}

export function ProgressRing({ value, label, unit = '' }) {
  return <div className="ring" style={{ '--value': `${value * 3.6}deg` }}><div><strong>{value}%</strong><span>{label}</span>{unit && <small>{unit}</small>}</div></div>
}
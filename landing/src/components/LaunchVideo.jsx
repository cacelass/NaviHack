import { useRef, useState } from 'react'
import Icon from './Icon.jsx'
import { video } from '../data.js'

// The launch video, inside its bento card. Nothing downloads until someone presses play
// (preload none); then it plays with sound and shows the native controls. The words on screen
// are the narration, so it still reads with the sound off.
export default function LaunchVideo() {
  const ref = useRef(null)
  const [started, setStarted] = useState(false)
  const play = () => {
    setStarted(true)
    ref.current?.play()
  }
  return (
    <div className="launch-box">
      <div className="launch-frame">
        <video
          ref={ref}
          src={video.src}
          poster={video.poster}
          preload="none"
          playsInline
          controls={started}
          width="1920"
          height="1080"
          aria-label={video.label}
        />
      </div>
      {!started && (
        <button type="button" className="btn btn-gold launch-play" onClick={play} aria-label={video.play}>
          <Icon name="play" size={16} />
          <span className="launch-len">{video.length}</span>
        </button>
      )}
    </div>
  )
}

import { useRef, useState } from 'react'
import Icon from './Icon.jsx'
import { video } from '../data.js'

// The launch video under the hero. Nothing downloads until someone presses play (preload none);
// then it plays with sound and shows the native controls. The words on screen are the narration,
// so it still reads with the sound off.
export default function LaunchVideo() {
  const ref = useRef(null)
  const [started, setStarted] = useState(false)
  const play = () => {
    setStarted(true)
    ref.current?.play()
  }
  return (
    <section className="launch" aria-label={video.label}>
      <div className="wrap">
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
            />
          </div>
          {!started && (
            <button type="button" className="btn btn-gold btn-lg launch-play" onClick={play}>
              <Icon name="play" size={18} />
              {video.play}
              <span className="launch-len">{video.length}</span>
            </button>
          )}
        </div>
      </div>
    </section>
  )
}

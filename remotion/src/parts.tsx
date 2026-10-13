// 画面零件：即梦片段、舞台背景、砸字、字幕、片头标识、钩子、质感层。
import React from 'react';
import {AbsoluteFill, Easing, Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, clamp, Line, MONO, outCubic, outExp, ramp, rnd, SANS, SERIF, useT, useV, win} from './lib';

// ---------- 即梦片段：缓慢推近 + 入场白闪；片段比镜头短时自动慢放 ----------
export const Clip: React.FC<{src: string; from: number; to: number; srcDur?: number; trim?: number; push?: number; first?: boolean}> = ({
	src,
	from,
	to,
	srcDur = 4,
	trim = 0,
	push = 0.08,
	first = false,
}) => {
	const t = useT();
	const {fps} = useVideoConfig();
	if (t < from - 0.05 || t > to + 0.45) return null;
	const a = first ? 1 - ramp(t, to + 0.05, to + 0.4, Easing.in(Easing.quad)) : win(t, from, to + 0.4, 0.25, 0.4);
	const p = clamp((t - from) / (to - from));
	const usable = Math.max(srcDur - trim - 0.1, 0.5);
	const rate = Math.max(0.55, Math.min(1, usable / Math.max(0.1, to + 0.4 - from)));
	const flash = first ? 0 : 1 - ramp(t, from, from + 0.18, outCubic);
	return (
		<AbsoluteFill style={{opacity: a}}>
			<AbsoluteFill style={{transform: `scale(${1.04 + push * p})`}}>
				<OffthreadVideo
					src={staticFile(src)}
					muted
					playbackRate={rate}
					trimBefore={Math.round(trim * fps)}
					style={{width: '100%', height: '100%', objectFit: 'cover', filter: 'saturate(0.95) contrast(1.08)'}}
				/>
			</AbsoluteFill>
			<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.35) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 60%, rgba(0,0,0,.7) 100%)'}} />
			<AbsoluteFill style={{background: '#fff', opacity: flash * 0.35, mixBlendMode: 'screen'}} />
		</AbsoluteFill>
	);
};

// ---------- 静态图：缓慢推近 ----------
export const Still: React.FC<{src: string; from: number; to: number; push?: number}> = ({src, from, to, push = 0.06}) => {
	const t = useT();
	if (t < from - 0.05 || t > to + 0.45) return null;
	const a = win(t, from, to + 0.4, 0.3, 0.4);
	const p = clamp((t - from) / (to - from));
	return (
		<AbsoluteFill style={{opacity: a}}>
			<Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${1.03 + push * p})`}} />
			<AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(0,0,0,.3) 0%, rgba(0,0,0,0) 30%, rgba(0,0,0,0) 60%, rgba(0,0,0,.7) 100%)'}} />
		</AbsoluteFill>
	);
};

// ---------- 舞台：暗场 + 一束顶光 + 漂浮尘埃（信息图的背景） ----------
export const Stage: React.FC<{beam?: number}> = ({beam = 0.8}) => {
	const t = useT();
	const {W, H, u} = useV();
	const light = '255,200,140';
	const dust = Array.from({length: 40}, (_, i) => {
		const px = W * 0.25 + rnd(i, 1) * W * 0.5 + Math.sin(t * 0.3 + i) * 30 * u;
		const py = ((rnd(i, 2) * H - t * (8 + rnd(i, 3) * 14) * u) % H + H) % H;
		const s = (1 + rnd(i, 4) * 3) * u;
		return <div key={i} style={{position: 'absolute', left: px, top: py, width: s, height: s, borderRadius: 9, background: `rgba(${light},${0.25 + rnd(i, 5) * 0.45})`, boxShadow: `0 0 ${s * 3}px rgba(${light},.6)`}} />;
	});
	return (
		<AbsoluteFill style={{background: 'radial-gradient(ellipse 60% 80% at 50% 30%, #1E140B 0%, #070504 70%)'}}>
			<AbsoluteFill
				style={{
					opacity: 0.55 * beam,
					background: `conic-gradient(from 180deg at 50% -8%, rgba(${light},0) 160deg, rgba(${light},.16) 172deg, rgba(${light},.22) 180deg, rgba(${light},.16) 188deg, rgba(${light},0) 200deg)`,
					filter: 'blur(14px)',
				}}
			/>
			<AbsoluteFill style={{opacity: beam}}>{dust}</AbsoluteFill>
		</AbsoluteFill>
	);
};

/** 场景容器：[from,to] 内可见，淡入淡出 + 缓慢推镜 */
export const Scene: React.FC<{from: number; to: number; children: React.ReactNode; zoom?: number}> = ({from, to, children, zoom = 0.03}) => {
	const t = useT();
	if (t < from - 0.05 || t > to + 0.45) return null;
	const a = win(t, from, to + 0.4, 0.35, 0.4);
	const p = clamp((t - from) / (to - from));
	return <AbsoluteFill style={{opacity: a, transform: `scale(${1 + zoom * p})`}}>{children}</AbsoluteFill>;
};

// ---------- 砸下来的大字 ----------
export const Slam: React.FC<{text: string; at: number; to: number; size?: number; color?: string; y?: number; glow?: boolean; font?: string; spacing?: number}> = ({
	text,
	at,
	to,
	size = 160,
	color = C.ivory,
	y = 0,
	glow = true,
	font = SERIF,
	spacing = 8,
}) => {
	const t = useT();
	const {u} = useV();
	const a = win(t, at, to, 0.08, 0.3);
	if (a <= 0) return null;
	const p = ramp(t, at, at + 0.28, outExp);
	const shake = t - at < 0.3 ? Math.sin((t - at) * 90) * 8 * u * (1 - p) : 0;
	return (
		<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `translate(${shake}px, ${y * u}px)`}}>
			<div
				style={{
					fontFamily: font,
					fontWeight: 900,
					fontSize: size * u,
					color,
					letterSpacing: spacing * u,
					opacity: a,
					transform: `scale(${1.6 - 0.6 * p})`,
					filter: `blur(${(1 - p) * 10}px)`,
					textShadow: glow ? `0 0 40px ${color}88, 0 0 120px ${color}44, 0 4px 30px rgba(0,0,0,.8)` : '0 4px 30px rgba(0,0,0,.8)',
					whiteSpace: 'nowrap',
				}}
			>
				{text}
			</div>
		</AbsoluteFill>
	);
};

// ---------- 字幕：逐字浮现；【】行为金色 ----------
export const Subs: React.FC<{lines: Line[]; quiet: [number, number][]}> = ({lines, quiet}) => {
	const t = useT();
	const {v, u} = useV();
	if (quiet.some(([a, b]) => t >= a && t < b + 0.3)) return null;
	const l = lines.find((x) => t >= x.s - 0.05 && t < x.e + 0.12);
	if (!l) return null;
	const a = win(t, l.s - 0.05, l.e + 0.12, 0.16, 0.12);
	const local = t - l.s;
	const chars = [...l.t.replace(/[，。；：、]$/, '')];
	return (
		<div style={{position: 'absolute', left: 40 * u, right: 40 * u, bottom: v ? 330 * u : 70 * u, textAlign: 'center', opacity: a}}>
			<span
				style={{
					fontFamily: SERIF,
					fontWeight: 700,
					fontSize: (v ? 58 : 50) * u,
					letterSpacing: 3 * u,
					color: l.emph ? C.goldHi : C.ivory,
					lineHeight: 1.4,
					textShadow: '0 2px 18px rgba(0,0,0,.95), 0 0 3px rgba(0,0,0,.9)',
				}}
			>
				{chars.map((ch, i) => {
					const ci = clamp((local - i * 0.022) / 0.2);
					return (
						<span key={i} style={{display: 'inline-block', opacity: ci, transform: `translateY(${(1 - ci) * 10}px)`, filter: `blur(${(1 - ci) * 4}px)`}}>
							{ch}
						</span>
					);
				})}
			</span>
		</div>
	);
};

// ---------- 片头标识：合集名 + 标题，居中出现后收到左上角（corner 模式第 0 帧就在角上） ----------
export const Lockup: React.FC<{series: string; title: string; hideAt: number; corner?: boolean}> = ({series, title, hideAt, corner = false}) => {
	const t = useT();
	const {W, H, v, u} = useV();
	const hide = 1 - ramp(t, hideAt - 0.3, hideAt);
	if (hide <= 0) return null;
	const p = corner ? 1 : ramp(t, 0.9, 1.6, Easing.inOut(Easing.cubic));
	const pin = corner ? 1 : outExp(clamp(t / 0.35));
	const x0 = W / 2,
		y0 = v ? H * 0.2 : H * 0.3;
	const x1 = (v ? 70 : 60) * u,
		y1 = (v ? 170 : 58) * u;
	const s = 1 - p * 0.72;
	return (
		<div
			style={{
				opacity: hide,
				position: 'absolute',
				left: x0 + (x1 - x0) * p,
				top: y0 + (y1 - y0) * p,
				transform: `translate(${-50 * (1 - p)}%, 0) scale(${s * (1.25 - 0.25 * pin)})`,
				transformOrigin: p > 0.5 ? '0 0' : '50% 0',
				textAlign: p > 0.5 ? 'left' : 'center',
				whiteSpace: 'nowrap',
				filter: `blur(${(1 - pin) * 3}px)`,
			}}
		>
			<div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 92 * u, letterSpacing: 26 * u, color: C.gold, textShadow: `0 0 40px ${C.gold}aa, 0 4px 24px rgba(0,0,0,.9)`, lineHeight: 1.15}}>{series}</div>
			<div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 150 * u, letterSpacing: 14 * u, color: C.ivory, textShadow: '0 0 40px rgba(255,255,255,.3), 0 6px 40px rgba(0,0,0,.95)', lineHeight: 1.15}}>{title}</div>
		</div>
	);
};

// ---------- 钩子：片头砸出的问句，最后一行放大成金色 ----------
export const Hook: React.FC<{lines: string[]; at: number; to: number}> = ({lines, at, to}) => {
	const t = useT();
	const {v, u} = useV();
	const a = win(t, at, to, 0.08, 0.35);
	if (a <= 0) return null;
	const hi = lines.length - 1;
	return (
		<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: a, padding: `0 ${50 * u}px`}}>
			<div style={{transform: `translateY(${v ? -120 * u : 20 * u}px)`, textAlign: 'center'}}>
				{lines.map((l, i) => {
					const p = ramp(t, at + i * 0.25, at + i * 0.25 + 0.3, outExp);
					const big = i === hi && lines.length > 1;
					return (
						<div
							key={i}
							style={{
								fontFamily: SERIF,
								fontWeight: 900,
								fontSize: (big ? (v ? 120 : 132) : 84) * u,
								color: big || lines.length === 1 ? C.goldHi : C.ivory,
								lineHeight: 1.3,
								opacity: p,
								transform: `scale(${1.5 - 0.5 * p})`,
								filter: `blur(${(1 - p) * 10}px)`,
								textShadow: big ? `0 0 40px ${C.gold}99, 0 6px 30px rgba(0,0,0,.95)` : '0 6px 30px rgba(0,0,0,.95)',
							}}
						>
							{l}
						</div>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

// ---------- 质感层：暗角 + 胶片颗粒 + 角标 ----------
export const Finish: React.FC<{signature?: string; badge?: boolean}> = ({signature, badge = true}) => {
	const f = useCurrentFrame();
	const {W, H, u} = useV();
	const seed = (f * 7) % 97;
	return (
		<>
			<AbsoluteFill style={{background: 'radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,.62) 100%)', pointerEvents: 'none'}} />
			<AbsoluteFill style={{opacity: 0.11, mixBlendMode: 'overlay'}}>
				<svg width={W} height={H}>
					<filter id={`g${seed}`}>
						<feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={seed} stitchTiles="stitch" />
						<feColorMatrix type="saturate" values="0" />
					</filter>
					<rect width={W} height={H} filter={`url(#g${seed})`} />
				</svg>
			</AbsoluteFill>
			{badge && (
				<div style={{position: 'absolute', left: 30 * u, top: 26 * u, padding: `${4 * u}px ${12 * u}px`, border: `${1.5 * u}px solid rgba(237,230,214,.35)`, borderRadius: 8 * u, fontFamily: SANS, fontSize: 20 * u, color: 'rgba(237,230,214,.5)'}}>AI生成</div>
			)}
			{signature && (
				<div style={{position: 'absolute', right: 46 * u, top: 38 * u, fontFamily: SANS, fontSize: 20 * u, letterSpacing: 6 * u, color: 'rgba(237,230,214,.42)', fontWeight: 600}}>{signature}</div>
			)}
		</>
	);
};

export {MONO};

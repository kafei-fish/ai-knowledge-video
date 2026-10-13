// 信息图：收益矩阵（逐格亮起）、条形对比（逐条长出）、大数字（滚动计数）、字卡、结尾金句卡。
import React from 'react';
import {AbsoluteFill, Easing} from 'remotion';
import {C, clamp, MONO, outBack, outExp, ramp, SERIF, Shot, useT, useV, win} from './lib';

const has = (list: number[][] | undefined, r: number, c: number) => !!list?.some(([a, b]) => a === r && b === c);

/** 一组连续的 matrix 镜头当成同一张矩阵：每个镜头只改变亮哪几格，格子平滑过渡而不是整张切换 */
export const Matrix: React.FC<{steps: Shot[]}> = ({steps}) => {
	const t = useT();
	const {W, H, v, u} = useV();
	const m = steps[0];
	const rows = m.rows!,
		cols = m.cols!,
		cells = m.cells!;
	const t0 = m.start;
	const cw = Math.min((v ? W * 0.82 : W * 0.5) / cols.length, 470 * u);
	const ch = Math.min((v ? H * 0.3 : H * 0.5) / rows.length, 230 * u);
	const x0 = (W - cw * cols.length) / 2 + 60 * u;
	const y0 = (H - ch * rows.length) / 2 - (v ? 80 : 20) * u;
	// 每格在每个步骤里的点亮程度，步骤之间交叉过渡
	const level = (pick: (s: Shot) => number[][] | undefined, r: number, c: number) =>
		Math.max(0, ...steps.map((s) => (has(pick(s), r, c) ? win(t, s.start, s.end + 0.3, 0.3, 0.3) : 0)));
	const title = steps.find((s) => s.title)?.title;
	return (
		<AbsoluteFill>
			{title && (
				<div style={{position: 'absolute', left: 0, right: 0, top: y0 - 150 * u, textAlign: 'center', fontFamily: SERIF, fontWeight: 900, fontSize: 44 * u, color: C.gold, letterSpacing: 4 * u, opacity: ramp(t, t0, t0 + 0.5)}}>
					{title}
				</div>
			)}
			{cols.map((c, j) => (
				<div key={c} style={{position: 'absolute', left: x0 + cw * j, width: cw, top: y0 - 62 * u, textAlign: 'center', fontFamily: SERIF, fontWeight: 700, fontSize: 36 * u, color: C.dim, opacity: ramp(t, t0 + 0.1 + j * 0.1, t0 + 0.6 + j * 0.1)}}>
					{c}
				</div>
			))}
			{rows.map((r, i) => (
				<div key={r} style={{position: 'absolute', left: x0 - 260 * u, width: 230 * u, top: y0 + ch * i + ch / 2 - 24 * u, textAlign: 'right', fontFamily: SERIF, fontWeight: 700, fontSize: 36 * u, color: C.dim, opacity: ramp(t, t0 + 0.2 + i * 0.1, t0 + 0.7 + i * 0.1)}}>
					{r}
				</div>
			))}
			{rows.map((_, i) =>
				cols.map((__, j) => {
					const k = i * cols.length + j;
					const pop = ramp(t, t0 + 0.15 + k * 0.08, t0 + 0.55 + k * 0.08, outBack);
					const hi = level((s) => s.highlight, i, j);
					const dim = level((s) => s.dim, i, j) * (1 - hi);
					// 刚亮起时数字放大一下
					const kick = Math.max(0, ...steps.map((s) => (has(s.highlight, i, j) ? 1 - ramp(t, s.start + 0.15, s.start + 0.7) : 0))) * hi;
					return (
						<div
							key={k}
							style={{
								position: 'absolute',
								left: x0 + cw * j + 10 * u,
								top: y0 + ch * i + 10 * u,
								width: cw - 20 * u,
								height: ch - 20 * u,
								borderRadius: 22 * u,
								border: `${2 * u}px solid ${hi > 0.01 ? `rgba(232,194,119,${0.35 + 0.65 * hi})` : 'rgba(237,230,214,.18)'}`,
								background: `rgba(${Math.round(14 + 66 * hi)},${Math.round(13 + 45 * hi)},${Math.round(11 + 7 * hi)},${0.72 + 0.1 * hi})`,
								boxShadow: hi > 0.01 ? `0 0 ${70 * hi * u}px ${C.gold}88` : 'none',
								opacity: pop * (1 - 0.55 * dim),
								transform: `scale(${(0.85 + 0.15 * pop) * (1 + 0.04 * hi)})`,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
							}}
						>
							<div style={{fontFamily: MONO, fontWeight: 700, fontSize: 84 * u, color: hi > 0.5 ? C.goldHi : C.ivory, transform: `scale(${1 + 0.25 * kick})`, textShadow: hi > 0.5 ? `0 0 30px ${C.gold}` : 'none'}}>
								{cells[i][j]}
							</div>
						</div>
					);
				}),
			)}
			{steps.map((s) =>
				s.note ? (
					<div
						key={s.id}
						style={{
							position: 'absolute',
							left: 60 * u,
							right: 60 * u,
							top: y0 + ch * rows.length + 34 * u,
							textAlign: 'center',
							fontFamily: SERIF,
							fontWeight: 900,
							fontSize: 46 * u,
							color: C.goldHi,
							textShadow: `0 0 30px ${C.gold}88`,
							opacity: win(t, s.start + 0.1, s.end + 0.2, 0.3, 0.25),
						}}
					>
						{s.note}
					</div>
				) : null,
			)}
		</AbsoluteFill>
	);
};

/** 条形对比：逐条从左长出，高亮的一条发金光，数值跟着滚动 */
export const Bars: React.FC<{shot: Shot}> = ({shot}) => {
	const t = useT();
	const {W, H, u} = useV();
	const items = shot.items!;
	const vmax = Math.max(...items.map((x) => Math.abs(x.value)), 1e-6);
	const bw = W * 0.5;
	const x0 = (W - bw) / 2 + 80 * u;
	const step = Math.min(150 * u, (H * 0.6) / items.length);
	const y0 = H / 2 - (step * (items.length - 1)) / 2 + 30 * u;
	const decimals = items.some((x) => !Number.isInteger(x.value)) ? 1 : 0;
	return (
		<AbsoluteFill>
			{shot.title && <div style={{position: 'absolute', left: 0, right: 0, top: y0 - 170 * u, textAlign: 'center', fontFamily: SERIF, fontWeight: 900, fontSize: 48 * u, color: C.gold}}>{shot.title}</div>}
			{items.map((it, k) => {
				const g = ramp(t, shot.start + 0.2 + k * 0.35, shot.start + 1.2 + k * 0.35, outExp);
				const on = it.label === (shot as any).highlight;
				const L = Math.max((bw * Math.abs(it.value)) / vmax, 6 * u) * g;
				const y = y0 + k * step;
				return (
					<React.Fragment key={it.label}>
						<div style={{position: 'absolute', left: x0 - 330 * u, width: 300 * u, top: y - 30 * u, textAlign: 'right', fontFamily: SERIF, fontWeight: 700, fontSize: 46 * u, color: C.ivory, opacity: ramp(t, shot.start + k * 0.2, shot.start + 0.4 + k * 0.2)}}>
							{it.label}
						</div>
						<div style={{position: 'absolute', left: x0, top: y - 26 * u, width: L, height: 52 * u, borderRadius: 12 * u, background: on ? `linear-gradient(90deg, ${C.gold}, ${C.goldHi})` : 'rgba(237,230,214,.32)', boxShadow: on ? `0 0 ${40 * u}px ${C.gold}aa` : 'none'}} />
						<div style={{position: 'absolute', left: x0 + L + 24 * u, top: y - 34 * u, fontFamily: MONO, fontWeight: 700, fontSize: 54 * u, color: on ? C.goldHi : C.ivory, opacity: g}}>
							{(it.value * g).toFixed(decimals)}
							{shot.unit || ''}
						</div>
					</React.Fragment>
				);
			})}
		</AbsoluteFill>
	);
};

/** 大数字：开头的数字从 0 滚动到目标值，后面的单位原样显示 */
export const BigNumber: React.FC<{shot: Shot}> = ({shot}) => {
	const t = useT();
	const {u} = useV();
	const m = (shot.big || '').match(/^([-+]?\d+(?:\.\d+)?)(.*)$/);
	const p = ramp(t, shot.start + 0.1, shot.start + 1.1, Easing.out(Easing.cubic));
	let text = shot.big || '';
	if (m) {
		const target = parseFloat(m[1]);
		const dec = m[1].includes('.') ? m[1].split('.')[1].length : 0;
		text = (target * p).toFixed(dec) + m[2];
	}
	const land = ramp(t, shot.start + 1.0, shot.start + 1.3, outBack);
	return (
		<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center'}}>
			{shot.title && <div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 46 * u, color: C.gold, marginBottom: 20 * u, opacity: ramp(t, shot.start, shot.start + 0.4)}}>{shot.title}</div>}
			<div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 230 * u, color: C.goldHi, transform: `scale(${0.9 + 0.1 * land + 0.06 * (1 - Math.abs(land - 1))})`, textShadow: `0 0 60px ${C.gold}99, 0 6px 40px rgba(0,0,0,.9)`, whiteSpace: 'nowrap'}}>{text}</div>
			{shot.caption && <div style={{fontFamily: SERIF, fontWeight: 700, fontSize: 52 * u, color: C.ivory, marginTop: 24 * u, opacity: ramp(t, shot.start + 0.9, shot.start + 1.4)}}>{shot.caption}</div>}
		</AbsoluteFill>
	);
};

/** 字卡：每行依次砸出，gold 指定金色行 */
export const Card: React.FC<{shot: Shot}> = ({shot}) => {
	const t = useT();
	const {v, u} = useV();
	const lines = shot.lines || [];
	const size = (shot.size || (lines.length > 1 ? 96 : 150)) * (v ? 0.9 : 1);
	return (
		<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: `0 ${60 * u}px`}}>
			<div style={{textAlign: 'center'}}>
				{lines.map((l, i) => {
					const p = ramp(t, shot.start + i * 0.6, shot.start + i * 0.6 + 0.35, outExp);
					const gold = (shot.gold || []).includes(i);
					return (
						<div
							key={i}
							style={{
								fontFamily: SERIF,
								fontWeight: 900,
								fontSize: size * u,
								letterSpacing: (lines.length === 1 ? 16 : 4) * u,
								color: gold ? C.goldHi : C.ivory,
								lineHeight: 1.35,
								opacity: p,
								transform: `scale(${1.4 - 0.4 * p})`,
								filter: `blur(${(1 - p) * 10}px)`,
								textShadow: gold ? `0 0 50px ${C.gold}aa, 0 6px 30px rgba(0,0,0,.9)` : '0 6px 30px rgba(0,0,0,.9)',
							}}
						>
							{l}
						</div>
					);
				})}
				{shot.sub && <div style={{marginTop: 40 * u, fontFamily: SERIF, fontWeight: 700, fontSize: 40 * u, letterSpacing: 10 * u, color: C.dim, opacity: ramp(t, shot.start + lines.length * 0.6, shot.start + lines.length * 0.6 + 0.5)}}>{shot.sub}</div>}
			</div>
		</AbsoluteFill>
	);
};

/** 叠在任何镜头上的弹字（storyboard 里写 pop），如「+10 份食物」 */
export const Pop: React.FC<{shot: Shot}> = ({shot}) => {
	const t = useT();
	const {u} = useV();
	const at = shot.start + 0.4;
	const a = win(t, at, shot.end, 0.08, 0.3);
	if (a <= 0 || !shot.pop) return null;
	const p = ramp(t, at, at + 0.28, outExp);
	const color = shot.pop_color === 'red' ? C.red : shot.pop_color === 'ivory' ? C.ivory : C.goldHi;
	const shake = t - at < 0.3 ? Math.sin((t - at) * 90) * 8 * u * (1 - p) : 0;
	return (
		<AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', transform: `translate(${shake}px, ${-220 * u}px)`}}>
			<div style={{fontFamily: SERIF, fontWeight: 900, fontSize: 110 * u, color, opacity: a, transform: `scale(${1.6 - 0.6 * p})`, filter: `blur(${(1 - p) * 10}px)`, textShadow: `0 0 40px ${color}88, 0 4px 30px rgba(0,0,0,.8)`, whiteSpace: 'nowrap'}}>
				{shot.pop}
			</div>
		</AbsoluteFill>
	);
};

export {clamp};

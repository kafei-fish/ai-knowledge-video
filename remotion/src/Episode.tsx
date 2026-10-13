// 整期成片：按 props 里的镜头表排布画面，叠加片头、字幕、质感层和声音。
import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {Bars, BigNumber, Card, Matrix, Pop} from './infographics';
import {C, Props, Shot, win} from './lib';
import {Clip, Finish, Hook, Lockup, Scene, Stage, Still, Subs} from './parts';

/** 把连续、内容相同的 matrix 镜头合成一组，矩阵就能逐格变化而不是整张切换 */
const groupShots = (shots: Shot[]) => {
	const out: Shot[][] = [];
	for (const s of shots) {
		const last = out[out.length - 1];
		const same =
			last &&
			s.type === 'matrix' &&
			last[0].type === 'matrix' &&
			JSON.stringify(last[0].cells) === JSON.stringify(s.cells) &&
			JSON.stringify(last[0].rows) === JSON.stringify(s.rows);
		if (same) last.push(s);
		else out.push([s]);
	}
	return out;
};

export const Episode: React.FC<Props> = (p) => {
	const {fps} = useVideoConfig();
	const groups = groupShots(p.shots);
	const b = p.brief;
	const firstEnd = p.shots.length > 1 ? p.shots[1].start : p.total;
	const hook = (b.header?.hook || '').split('|').filter(Boolean);
	const corner = b.header?.style === 'corner';
	const last = p.shots[p.shots.length - 1];
	const lockHide = last && last.type === 'card' ? last.start : p.total;
	const quiet = p.shots.filter((s) => s.hide_subs).map((s) => [s.start, s.end] as [number, number]);

	return (
		<AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
			{groups.map((g, gi) => {
				const s = g[0];
				const from = s.start;
				const to = g[g.length - 1].end;
				if (s.type === 'clip')
					return <Clip key={s.id} src={s.src!} from={from} to={to} srcDur={s.srcDur} trim={s.trim} push={s.push ?? 0.1} first={gi === 0} />;
				if (s.type === 'image') return <Still key={s.id} src={s.src!} from={from} to={to} push={s.push} />;
				return (
					<Scene key={s.id} from={from} to={to}>
						<Stage beam={0.75} />
						{s.type === 'matrix' && <Matrix steps={g} />}
						{s.type === 'bars' && <Bars shot={s} />}
						{s.type === 'number' && <BigNumber shot={s} />}
						{s.type === 'card' && <Card shot={s} />}
					</Scene>
				);
			})}
			{p.shots.map((s) => (s.pop ? <Pop key={`pop-${s.id}`} shot={s} /> : null))}

			{hook.length > 0 && !corner && <Hook lines={hook} at={1.3} to={Math.max(firstEnd, 3.2)} />}
			{hook.length > 0 && corner && <Hook lines={hook} at={0} to={Math.max(firstEnd, 3.2)} />}
			{(b.series || b.title) && <Lockup series={[b.series, b.episode].filter(Boolean).join(' · ')} title={b.title || ''} hideAt={lockHide} corner={corner} />}
			<Subs lines={p.lines} quiet={quiet} />
			<Finish signature={b.signature} badge={b.badge !== false} />

			{p.music && <Audio src={staticFile(p.music)} volume={(f) => musicGain(p, f / fps)} />}
			{p.segments.map((s) => (
				<Sequence key={s.id} from={Math.round(s.at * fps)} layout="none">
					<Audio src={staticFile(s.file)} />
				</Sequence>
			))}
		</AbsoluteFill>
	);
};

/** 人声出现时把音乐压低（平滑过渡），结尾淡出 */
const musicGain = (p: Props, t: number) => {
	const talk = Math.max(0, ...p.segments.map((s) => win(t, s.at - 0.3, s.at + s.dur + 0.3, 0.4, 0.4)));
	const fade = Math.min(1, Math.max(0, (p.total - t) / 2.5));
	return (0.55 - 0.25 * talk) * fade;
};

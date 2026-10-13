// 公共：配色、字体、缓动、时间与画幅工具。改编自「Leo的反常识课」已发布作品的组件。
import {Easing, useCurrentFrame, useVideoConfig} from 'remotion';

export const C = {
	bg: '#07080B',
	ivory: '#EDE6D6',
	dim: '#8A8578',
	gold: '#E8C277',
	goldHi: '#FFE2A3',
	red: '#FF4D3D',
};
export const SERIF = '"Songti SC","STSongti-SC-Bold","Source Han Serif SC","Noto Serif CJK SC","SimSun",serif';
export const SANS = '"PingFang SC","Noto Sans CJK SC","Source Han Sans SC","Microsoft YaHei",sans-serif';
export const MONO = '"SF Mono","JetBrains Mono","DejaVu Sans Mono",Menlo,Consolas,monospace';

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const ramp = (t: number, a: number, b: number, ease: (x: number) => number = Easing.inOut(Easing.cubic)) =>
	ease(clamp((t - a) / Math.max(b - a, 1e-6)));
export const outBack = Easing.out(Easing.back(1.6));
export const outCubic = Easing.out(Easing.cubic);
export const outExp = Easing.out(Easing.exp);
/** [a,b] 内可见，带淡入淡出 */
export const win = (t: number, a: number, b: number, fi = 0.35, fo = 0.35) =>
	Math.min(ramp(t, a, a + fi, outCubic), 1 - ramp(t, b - fo, b, Easing.in(Easing.quad)));

export const useT = () => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	return f / fps;
};
/** W/H 画幅，v 是否竖屏，u 以 1080 为基准的缩放系数 */
export const useV = () => {
	const {width, height} = useVideoConfig();
	return {W: width, H: height, v: height > width, u: Math.min(width, height) / 1080};
};

/** 固定种子伪随机（逐帧可复现，不用 Math.random） */
export const rnd = (i: number, n: number) => {
	const x = Math.sin(i * 127.1 + n * 311.7) * 43758.5453;
	return x - Math.floor(x);
};

// ---------- 数据类型（由 scripts/remotion_render.py 生成的 props） ----------
export type Line = {seg: string; i: number; t: string; emph: boolean; s: number; e: number};
export type Shot = {
	id: string;
	type: 'clip' | 'image' | 'card' | 'number' | 'matrix' | 'bars';
	start: number;
	end: number;
	src?: string;
	srcDur?: number;
	trim?: number;
	push?: number;
	hide_subs?: boolean;
	lines?: string[];
	gold?: number[];
	sub?: string;
	size?: number;
	big?: string;
	caption?: string;
	title?: string;
	note?: string;
	rows?: string[];
	cols?: string[];
	cells?: string[][];
	highlight?: number[][];
	dim?: number[][];
	items?: {label: string; value: number}[];
	unit?: string;
	pop?: string;
	pop_color?: 'gold' | 'red' | 'ivory';
};
export type Props = {
	total: number;
	brief: {
		series?: string;
		episode?: string;
		title?: string;
		signature?: string;
		badge?: boolean;
		header?: {hook?: string; style?: 'center' | 'corner'};
	};
	segments: {id: string; at: number; dur: number; file: string}[];
	lines: Line[];
	shots: Shot[];
	music?: string;
};

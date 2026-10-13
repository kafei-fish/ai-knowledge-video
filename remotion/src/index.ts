import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Episode} from './Episode';
import type {Props} from './lib';

const blank: Props = {total: 5, brief: {title: '预览'}, segments: [], lines: [], shots: [{id: 's01', type: 'card', start: 0, end: 5, lines: ['用 remotion_render.py 传入工程']}]};

const Root: React.FC = () =>
	React.createElement(Composition as any, {
		id: 'Episode',
		component: Episode,
		fps: 30,
		width: 1920,
		height: 1080,
		durationInFrames: 150,
		defaultProps: blank,
		calculateMetadata: ({props}: {props: Props & {w?: number; h?: number}}) => ({
			durationInFrames: Math.max(1, Math.round(props.total * 30)),
			width: props.w || 1920,
			height: props.h || 1080,
		}),
	});

registerRoot(Root);

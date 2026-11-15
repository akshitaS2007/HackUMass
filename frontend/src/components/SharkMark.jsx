import React from "react";


export default function SharkMark({ className = "" }) {
	return (
		<svg
			className={`shark-mark ${className}`.trim()}
			viewBox="0 0 100 60"
			role="img"
			aria-label="Shark"
		>
			<path
				className="shark-tail"
				d="M21 27 4 8l6 22-8 22 20-17Z"
			/>
			<path
				className="shark-body"
				d="M14 30c10-8 25-13 42-13 14 0 26 4 37 10l7 3-9 4c-9 2-15 7-20 14l-8-12c-14 3-30 1-43-5l-8 5 3-7-8-5Z"
			/>
			<path
				className="shark-belly"
				d="M21 33c14 6 29 8 43 4l5 7c-7 5-16 7-25 4-9-3-17-8-23-15Z"
			/>
			<path className="shark-fin" d="m43 19 9-16 9 17c-6-1-12-1-18-1Z" />
			<path className="shark-fin-accent" d="m51 7 4 9" />
			<path className="shark-fin-small" d="m69 19 7-8 1 11Z" />
			<path className="shark-pectoral" d="M44 35c8 0 15 2 22 5L54 53c-2-7-6-13-10-18Z" />
			<path className="shark-gills" d="m73 25-2 8m6-7-2 8m6-7-2 7" />
			<circle className="shark-eye" cx="86" cy="26" r="1.6" />
			<path className="shark-mouth" d="m84 32 12-1" />
			<path className="shark-teeth" d="m87 31 2 3 2-3 2 3 2-3" />
		</svg>
	);
}

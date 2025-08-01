import React from 'react';
import './ZoneConfigPanel.css';

export default function ZoneConfigPanel({
  zones = [],            // 기본 빈 배열
  selected,
  onSelect,
  currentAction,
  onActionSelect,
  onDelete,
  onCancel
}) {
  return (
    <div className="zone-config">
      <div className="zone-config-header">
        <h3>위험 구역 관리</h3>
        <button className="btn-cancel" onClick={onCancel}>취소</button>
      </div>
      <div className="zone-config-buttons">
        <button
          className={currentAction === 'view' ? 'active' : ''}
          onClick={() => onActionSelect('view')}
        >조회</button>
        <button
          className={currentAction === 'create' ? 'active' : ''}
          onClick={() => onActionSelect('create')}
        >생성</button>
        <button
          disabled={!selected}
          className={currentAction === 'update' ? 'active' : ''}
          onClick={() => onActionSelect('update')}
        >업데이트</button>
        <button
          disabled={!selected}
          className={currentAction === 'delete' ? 'active' : ''}
          onClick={() => onActionSelect('delete')}
        >삭제</button>
      </div>
      <ul className="zone-list">
        {zones.length === 0 ? (
          <li className="empty">등록된 위험 구역이 없습니다.</li>
        ) : (
          zones.map(z => (
            <li
              key={z.id}
              className={z.id === selected ? 'selected' : ''}
              onClick={() => onSelect(z.id)}
            >
              {z.name || `Zone ${z.id}`}
            </li>
          ))
        )}
      </ul>
    </div>
  );
}

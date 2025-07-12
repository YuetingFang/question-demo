import React from 'react';
import PropTypes from 'prop-types';
import { Container } from 'react-bootstrap';

/**
 * 桌面端通用布局组件
 * 提供页面的基本结构：只保留主体内容区域
 */
function DesktopLayout({ 
  children, 
  title, // 保留title参数以便在需要时在界面上显示
  // 默认不显示页眉和页脚
  showHeader = false, 
  showFooter = false,
  footerContent = null 
}) {
  return (
    <div className="desktop-layout">
      <main className="desktop-content">
        <Container fluid className="content-container">
          {children}
        </Container>
      </main>
    </div>
  );
}

DesktopLayout.propTypes = {
  children: PropTypes.node.isRequired,
  title: PropTypes.string,
  showHeader: PropTypes.bool,
  showFooter: PropTypes.bool,
  footerContent: PropTypes.node
};

export default DesktopLayout;

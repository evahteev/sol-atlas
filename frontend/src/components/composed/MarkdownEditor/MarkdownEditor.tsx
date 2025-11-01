'use client'

import { FC } from 'react'

import {
  BlockTypeSelect,
  BoldItalicUnderlineToggles,
  CodeToggle,
  CreateLink,
  DiffSourceToggleWrapper,
  InsertImage,
  InsertTable,
  InsertThematicBreak,
  ListsToggle,
  MDXEditor,
  MDXEditorProps,
  Separator,
  UndoRedo,
  codeBlockPlugin,
  codeMirrorPlugin,
  diffSourcePlugin,
  headingsPlugin,
  imagePlugin,
  linkDialogPlugin,
  linkPlugin,
  listsPlugin,
  markdownShortcutPlugin,
  quotePlugin,
  tablePlugin,
  thematicBreakPlugin,
  toolbarPlugin,
} from '@mdxeditor/editor'
import clsx from 'clsx'

import { uploadFile } from '@/services/upload/upload'

import styles from './MarkdownEditor.module.scss'

export const MarkdownEditor: FC<MDXEditorProps & { classNames?: { toolbar?: string } }> = ({
  classNames,
  ...props
}) => {
  return (
    <MDXEditor
      {...props}
      className={clsx(props.className, 'dark-theme', 'dark-editor')}
      plugins={[
        toolbarPlugin({
          toolbarClassName: clsx(styles.toolbar, classNames?.toolbar),
          toolbarPosition: 'top',
          toolbarContents: () => (
            <DiffSourceToggleWrapper>
              <UndoRedo />
              <Separator />
              <BoldItalicUnderlineToggles />
              <CodeToggle />
              <Separator />
              <ListsToggle />
              <Separator />
              <BlockTypeSelect />
              <Separator />
              <CreateLink />
              <InsertImage />
              <Separator />
              <InsertTable />
              <InsertThematicBreak />
            </DiffSourceToggleWrapper>
          ),
        }),
        imagePlugin({ imageUploadHandler: uploadFile }),
        tablePlugin(),
        headingsPlugin(),
        listsPlugin(),
        quotePlugin(),
        thematicBreakPlugin(),
        markdownShortcutPlugin(),
        linkPlugin(),
        codeBlockPlugin(),
        codeMirrorPlugin(),
        linkDialogPlugin(),
        diffSourcePlugin({ viewMode: 'rich-text', diffMarkdown: props.markdown }),
      ]}
    />
  )
}
